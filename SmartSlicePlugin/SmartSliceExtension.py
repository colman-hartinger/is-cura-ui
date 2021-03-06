import os
import json
from typing import Dict

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Extension import Extension
from UM.PluginRegistry import PluginRegistry
from UM.Job import Job
from UM.FileHandler.ReadFileJob import ReadFileJob
from UM.Workspace.WorkspaceFileHandler import WorkspaceFileHandler
from UM.Scene.SceneNode import SceneNode
from UM.Message import Message

from cura.CuraApplication import CuraApplication

from .SmartSliceCloudConnector import SmartSliceCloudConnector
from .SmartSliceCloudProxy import SmartSliceCloudProxy
from .SmartSliceCloudStatus import SmartSliceCloudStatus
from .utils import getPrintableNodes, getModifierMeshes, intersectingNodes

import pywim

i18n_catalog = i18nCatalog("smartslice")


class SmartSliceExtension(Extension):

    def __init__(self):
        super().__init__()

        self.metadata = PluginMetaData()

        # Proxy to the UI, and the cloud connector for the cloud
        self.proxy = SmartSliceCloudProxy()
        self.cloud = SmartSliceCloudConnector(self.proxy, self)

        #self.setMenuName(i18n_catalog.i18nc("@item:inmenu", "Smart Slice"))

        # Help links
        self.addMenuItem(i18n_catalog.i18n("Help"), self._openHelp)
        self.addMenuItem(i18n_catalog.i18n("Contact"), self._contactHelp)

        # About Dialog
        self._about_dialog = None
        self.addMenuItem(i18n_catalog.i18nc("@item:inmenu", "About"), self._openAboutDialog)

        # Logout Menu Option
        self.addMenuItem(i18n_catalog.i18n("Logout"),
                         self.cloud.api_connection.logout)

        # Connection to the file writer on File->Save
        self._outputManager = Application.getInstance().getOutputDeviceManager()
        self._outputManager.writeStarted.connect(self._writeState)

        # Connection to File->Open after the mesh is loaded - this depends on if the user is loading a Cura project
        CuraApplication.getInstance().fileCompleted.connect(self._getState)
        Application.getInstance().workspaceLoaded.connect(self._getState)

        controller = Application.getInstance().getController()
        controller.getScene().getRoot().childrenChanged.connect(self._reset)

        Application.getInstance().engineCreatedSignal.connect(self._onEngineCreated)

        # Data storage location for workspaces - this is where we store our data for saving to the Cura project
        self._storage = Application.getInstance().getWorkspaceMetadataStorage()

        # We use the signal from the cloud connector to always update the plugin metadeta after results are generated
        # _saveState is also called when the user actually saves a project
        self.cloud.saveSmartSliceJob.connect(self._saveState)
        self._save_prompt = None
        self.proxy.closeSavePromptClicked.connect(self.onCloseSavePromptClicked)
        self.proxy.escapeSavePromptClicked.connect(self.onEscapeSavePromptClicked)
        self.proxy.savePromptClicked.connect(self.onSavePromptClicked)

        # The handle to the class which does all of the checks on application exit. Add our function to the callback list
        self._exitManager = CuraApplication.getInstance().getOnExitCallbackManager()
        self._exitManager.addCallback(self._saveOnExit)

    def _onEngineCreated(self):
        Application.getInstance()._job_queue.jobStarted.connect(self._workspaceLoading)

    @staticmethod
    def _openHelp():
        QDesktopServices.openUrl(QUrl("https://help.tetonsim.com"))

    @staticmethod
    def _contactHelp():
        QDesktopServices.openUrl(QUrl("mailto:help@tetonsim.com?subject=Request for help with Smart Slice"))

    def _openAboutDialog(self):
        if not self._about_dialog:
            self._about_dialog = self._createQmlDialog("SmartSliceAbout.qml", vars={"aboutText": self._aboutText()})
        self._about_dialog.show()

    def _closeAboutDialog(self):
        if not self._about_dialog:
            self._about_dialog.close()

    def _createQmlDialog(self, dialog_qml, directory = None, vars = None):
        if directory is None:
            directory = PluginRegistry.getInstance().getPluginPath(self.getPluginId())

        mainApp = Application.getInstance()

        return mainApp.createQmlComponent(os.path.join(directory, dialog_qml), vars)

    def _aboutText(self):
        about = 'Smart Slice for Cura\n'
        about += 'Version: {}'.format(self.metadata.version)
        return about

    # Function which is called on application exit
    def _saveOnExit(self, force_exit=False):

        if force_exit:
            if self._save_prompt:
                self._save_prompt.close()
            self._exitManager.onCurrentCallbackFinished(should_proceed=True)
            return

        cloudJob = self.cloud.cloudJob

        # Tell the exit manager to move on to the next callback if there are no unsaved results
        if not cloudJob or not cloudJob.getResult() or cloudJob.saved:
            if self._save_prompt:
                self._save_prompt.close()
            self._exitManager.onCurrentCallbackFinished(should_proceed=True)
            return

        # The user hasn't saved results - switch to the Smart Slice stage and prompt them to save
        else:
            controller = Application.getInstance().getController()
            active_stage = controller.getActiveStage()

            if not active_stage or active_stage.getPluginId() != self.metadata.id:
                controller.setActiveStage(self.metadata.id)

            if not self._save_prompt:
                self._save_prompt = self._createQmlDialog("SmartSliceSavePrompt.qml")

            self._save_prompt.show()

    def onCloseSavePromptClicked(self):
        self._saveOnExit(True)

    def onEscapeSavePromptClicked(self):
        self._exitManager.resetCurrentState()
        self._exitManager.onCurrentCallbackFinished(should_proceed=False)

    def onSavePromptClicked(self):
        try:
            self._save_prompt.close()

            save_args = {
                "filter_by_machine": False,
                "preferred_mimetypes": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"
            }

            # Get the local output file manager and write out the job as a 3MF as a workspace with
            # the Smart Slice data.
            self._outputManager.getOutputDevice("local_file").requestWrite(
                nodes=[Application.getInstance().getController().getScene().getRoot()],
                file_name=CuraApplication.getInstance().getPrintInformation().jobName,
                limit_mimetypes=None,
                file_handler=Application.getInstance().getWorkspaceFileHandler(),
                kwargs=save_args
            )

            self._saveOnExit(True)

        # This happens when a user exits the save dialog - we assume they want to cancel exiting
        # the main application
        except:
            self.onEscapeSavePromptClicked()

    def _writeState(self, output_object=None):
        self._saveState(True)

    def _saveState(self, writing_workspace=False):
        # Build the Smart Slice job. We want to always build in case something has changed
        job = self.cloud.smartSliceJobHandle.buildJobFor3mf()

        # No need to save aything if we haven't switched to the smart slice stage yet
        # This is the only time we will get a null job
        if not job:
            return

        cloudJob = self.cloud.cloudJob
        if cloudJob:
            job.type = cloudJob.job_type

        # Reset the status if we're saving during a run. In the future, we should try to pull
        # down the results when the user opens a project which was in the middle of running
        status = self.cloud.status
        if status in SmartSliceCloudStatus.busy():
            if job.type == pywim.smartslice.job.JobType.validation:
                status = SmartSliceCloudStatus.ReadyToVerify
            else:
                status = self.cloud.getProxy().optimizationStatus()

        # Place the job in the metadata under our plugin ID
        self._storage.setEntryToStore(plugin_id=self.metadata.id, key='job', data=job.to_dict())
        self._storage.setEntryToStore(plugin_id=self.metadata.id, key='version', data=self.metadata.version)
        self._storage.setEntryToStore(plugin_id=self.metadata.id, key='status', data=status.value)

        # Need to do some checks to see if we've stored the results for the active job
        if cloudJob and cloudJob.getResult():
            self._storage.setEntryToStore(plugin_id=self.metadata.id, key='results', data=cloudJob.getResult().to_dict())
            self._storage.setEntryToStore(
                plugin_id=self.metadata.id,
                key='selectedResult',
                data=self.proxy.resultsTable.getSelectedResultId()
            )
            if writing_workspace:
                cloudJob.saved = True
        elif job.type == pywim.smartslice.job.JobType.validation and (not cloudJob or not cloudJob.getResult()):
            self._storage.setEntryToStore(plugin_id=self.metadata.id, key='results', data=None)
            self._storage.setEntryToStore(plugin_id=self.metadata.id, key='selectedResult', data=None)

    # Acquires all of the smart slice data from Cura storage and updates the UI
    def _getState(self, filename=None):
        all_data = self._storage.getPluginMetadata(self.metadata.id)

        # No need to go further if we don't have any data stored
        if len(all_data) == 0:
            return

        # Send the user back to Prepare if they are in Smart Slice
        controller = Application.getInstance().getController()
        if controller.getActiveStage() and controller.getActiveStage().getPluginId() == self.metadata.id:
            controller.setActiveStage("PrepareStage")

        job_dict = all_data['job']
        status = all_data['status']
        results_dict = all_data.get('results', None)
        row = all_data.get('selectedResult', None) # The row is stored as the order of the results

        job = pywim.smartslice.job.Job.from_dict(job_dict) if job_dict else None
        results = pywim.smartslice.result.Result.from_dict(results_dict) if results_dict else None
        selected_row = row if row and row >= 0 else 0

        self.cloud.clearJobs()

        def afterSmartSliceNodeInit():
            if status:
                self.cloud.status = SmartSliceCloudStatus(status)

            else:
                self.proxy.updateStatusFromResults(job, results)
                self.cloud.updateStatus()

            if self.cloud.status == SmartSliceCloudStatus.Optimized:
                self.cloud.addJob(pywim.smartslice.job.JobType.optimization)
            else:
                self.cloud.addJob(pywim.smartslice.job.JobType.validation)

            if results:
                self.cloud.cloudJob.setResult(results)
                self.cloud.cloudJob.saved = True
                self.cloud.processAnalysisResult(selected_row)

            self.cloud.propertyHandler.resetProperties()
            self.cloud.updateSliceWidget()
            self.proxy.updateColorUI()

            self._storage.getPluginMetadata(self.metadata.id).clear()

        if job:
            self.proxy.updatePropertiesFromJob(job, afterSmartSliceNodeInit)

    def _reset(self, *args):
        if len(getPrintableNodes()) == 0:
            self._storage.getPluginMetadata(self.metadata.id).clear()

    def _workspaceLoading(self, job: Job):
        if isinstance(job, ReadFileJob):
            if job._handler and isinstance(job._handler, WorkspaceFileHandler):
                self._storage.getPluginMetadata(self.metadata.id).clear()
                self.cloud.propertyHandler.resetProperties()
                self.cloud.status = SmartSliceCloudStatus.Errors

class PluginMetaData:
    def __init__(self):
        self.name = 'Smart Slice Plugin'
        self.id = 'SmartSlicePlugin'
        self.version = 'N/A'
        self.url = 'https://api.smartslice.xyz'
        self.cluster = None

        pluginMetaData = PluginMetaData.getMetadata()

        if pluginMetaData:
            self.name = pluginMetaData.get('name', self.name)
            self.id = pluginMetaData.get('id', self.id)
            self.version = pluginMetaData.get('version', self.version)

            apiInfo = pluginMetaData.get('smartSliceApi', None)

            if apiInfo:
                self.url = apiInfo.get('url', self.url)
                self.cluster = apiInfo.get('cluster', self.cluster)

    @staticmethod
    def getMetadata() -> Dict[str, str]:
        try:
            plugin_json_path = os.path.dirname(os.path.abspath(__file__))
            plugin_json_path = os.path.join(plugin_json_path, 'plugin.json')
            with open(plugin_json_path, 'r') as f:
                plugin_info = json.load(f)
            return plugin_info
        except:
            return None

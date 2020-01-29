#   SmartSlicePropertyHandler.py
#   Teton Simulation
#   Authored on   January 3, 2019
#   Last Modified January 3, 2019

#
#  Contains procedures for handling Cura Properties in accordance with SmartSlice
#

import copy
from copy import copy

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtProperty
from PyQt5.QtCore import QObject

#  Cura
from UM.Application import Application
from UM.Preferences import Preferences
from UM.Settings.ContainerStack import ContainerStack
from UM.Scene.Selection import Selection
from UM.Logger import Logger
from cura.CuraApplication import CuraApplication
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator
from UM.Settings.SettingInstance import InstanceState


#  Smart Slice
from .SmartSliceCloudProxy import SmartSliceCloudStatus
from .SmartSliceValidationProperty import SmartSliceValidationProperty, SmartSliceLoadDirection

class SmartSlicePropertyHandler(QObject):
    def __init__(self, connector):
        super().__init__()

        #  Callback
        self.connector = connector
        self._confirming = False
        self._initialized = False
        
        self._activeMachineManager = CuraApplication.getInstance().getMachineManager()
        self._globalStack = self._activeMachineManager.activeMachine
        self._activeExtruder = self._globalStack.extruderList[0]
        
        #  Cache Space
        self._propertiesChanged = []
        self._changedValues     = []
        self._hasChanges = False


        #  Mesh Properties
        self.meshScale    = None
        self.newScale = None
        self.meshRotation = None
        self.newRotation = None


        self._selection_mode = 1 # Default to AnchorMode
        self._changedMesh = None
        self._changedFaces = None
        self._changedForce = None
        self._anchoredMesh = None
        self._anchoredFaces = None
        self._loadedMesh = None
        self._loadedFaces = None

        self._sceneNode = None
        self._sceneRoot = Application.getInstance().getController().getScene().getRoot()

        self._material = self._activeMachineManager._global_container_stack.extruderList[0].material #  Cura Material Node

        self._cancelChanges = False
        
        #  Connect Signals
        self._globalStack.propertyChanged.connect(self._onGlobalPropertyChanged)
        self._activeExtruder.propertyChanged.connect(self._onExtruderPropertyChanged)

        self._activeMachineManager.activeMaterialChanged.connect(self._onMaterialChanged)
        #Application.getInstance().getController().getScene().sceneChanged.connect(self._onModelChanged)

        self._sceneRoot.childrenChanged.connect(self.connectMeshSignals)
        
        self._global_cache = {}
        self._extruder_cache = {}


    def cacheGlobal(self):

        global_keys = {"layer_height_0", "layer_height"}

        self._global_cache = {}

        for key in global_keys:
            self._global_cache[key] = self._globalStack.getProperty(key, "value")
            #print ("\nSetting State:  " + str(self._globalStack.getProperty(key, "state")) + "\n")
            


    def cacheExtruder(self):
        
        extruder_keys = {"wall_line_width_0", "wall_line_width_x", "wall_line_width", "line_width", "wall_line_count", 
                         "skin_angles", "top_layers", "bottom_layers", 
                         "infill_pattern", "infill_sparse_density", "infill_angles", 
                         "alternate_extra_perimeter", "wall_thickness"}

        self._extruder_cache = {}

        for key in extruder_keys:
            self._extruder_cache[key] = self._activeExtruder.getProperty(key, "value")

    def cacheChanges(self):
        self.cacheGlobal()
        self.cacheExtruder()

    def restoreCache(self):

        for property in self._global_cache:
            self._globalStack.setProperty(property, "value", self._global_cache[property])
            #self._globalStack.setProperty(property, "state", InstanceState.Default)

        for property in self._extruder_cache:
            self._activeExtruder.setProperty(property, "value", self._extruder_cache[property])
            #self._activeExtruder.setProperty(property, "state", InstanceState.Default)

        print ("\nTest Property Cache:  " + str(self._activeExtruder.getProperty("infill_sparse_density", "value")) + "\n")


    def cancelChanges(self):
        self.restoreCache()
        self.connector._proxy.confirmationWindowEnabled = False
        self.connector._proxy.confirmationWindowEnabledChanged.emit()

    def confirmChanges(self):
        self.cacheChanges()


    #
    #   CONFIRM/CANCEL PROPERTY CHANGES
    #
    def _onConfirmChanges(self):
        for prop in self._propertiesChanged:
          #  Use-Case/Requirements
            if   prop is SmartSliceValidationProperty.MaxDisplacement:
                self.connector._proxy.reqsMaxDeflect = self.connector._proxy.targetMaximalDisplacement
            elif prop is SmartSliceValidationProperty.FactorOfSafety:
                self.connector._proxy.reqsSafetyFactor = self.connector._proxy.targetFactorOfSafety
            elif prop is SmartSliceValidationProperty.LoadDirection:
                self.connector._proxy.reqsLoadDirection = self.connector._proxy.loadDirection
            elif prop is SmartSliceValidationProperty.LoadMagnitude:
                self.connector._proxy.reqsLoadMagnitude = self.connector._proxy.loadMagnitude

          #  Face Selection
            elif prop is SmartSliceValidationProperty.SelectedFace:
                self.updateMeshes()
                self.selectedFacesChanged.emit()

          #  Material
            elif prop is SmartSliceValidationProperty.Material:
                self._material = self._changedValues.pop(0)
            elif prop is SmartSliceValidationProperty.MeshScale:
                self.meshScale = self._changedValues.pop(0)
            elif prop is SmartSliceValidationProperty.MeshRotation:
                self.meshRotation = self._changedValues.pop(0)
        
        self.confirmChanges()

        self.connector._proxy.confirmationWindowEnabled = False
        self.connector._proxy.confirmationWindowEnabledChanged.emit()


    def _onCancelChanges(self):
        self._cancelChanges = True
        #Logger.log(str(prop))
        for prop in self._propertiesChanged:
            print (str(prop))
          #  REQUIREMENTS / USE-CASE
            if prop is SmartSliceValidationProperty.FactorOfSafety:
                self.connector._proxy.setFactorOfSafety()
            elif prop is SmartSliceValidationProperty.MaxDisplacement:
                self.connector._proxy.setMaximalDisplacement()
            elif prop is SmartSliceValidationProperty.LoadMagnitude:
                self.connector._proxy.setLoadMagnitude()
            elif prop is SmartSliceValidationProperty.LoadDirection:
                self.connector._proxy.setLoadDirection()

            elif prop is SmartSliceValidationProperty.MeshScale:
                self.setMeshScale()
            elif prop is SmartSliceValidationProperty.MeshRotation:
                self.setMeshRotation()

          #  FACE SELECTION
            #  Selected Face(s)
                # Do Nothing
        
            #  Material Properties
            elif prop is SmartSliceValidationProperty.Material:
                self.setMaterial()

            self._propertiesChanged.pop(0)

        
        for i in self._changedValues:
            self._changedValues.pop(0)

        self.cancelChanges()

        self._cancelChanges = False

        self.connector._proxy.confirmationWindowEnabled = False
        self.connector._proxy.confirmationWindowEnabledChanged.emit()


    def getGlobalProperty(self, key):
        return self._global_cache[key]

    def getExtruderProperty(self, key):
        return self._extruder_cache[key]

    #
    #  LOCAL TRANSFORMATION PROPERTIES
    #

    def connectMeshSignals(self, unused):
        i = 0
        _root = self._sceneRoot 

        for node in _root.getAllChildren():
            print ("Node Found:  " + node.getName())
            if node.getName() == "3d":
                if (self._sceneNode is None) or (self._sceneNode.getName() != _root.getAllChildren()[i+1].getName()):
                    if self._sceneNode is not None:
                        self._sceneNode.transformationChanged.disconnectAll()

                    self._sceneNode = _root.getAllChildren()[i+1]
                    print ("\nFile Found:  " + self._sceneNode.getName() + "\n")

                    #  Set Initial Scale/Rotation
                    self.meshScale    = self._sceneNode.getScale()
                    self.meshRotation = self._sceneNode.getOrientation()

                    #  TODO: Properly Disconnect this Signal, when figure out where to do so
                    self._sceneNode.transformationChanged.connect(self._onLocalTransformationChanged)
                    i += 1
            
            i += 1

        # STUB
        return 


    #
    #  LOCAL TRANSFORMATION
    #

    def _onLocalTransformationChanged(self, node):
        if node.getScale() != self.meshScale:
            self.onMeshScaleChanged()
        if node.getOrientation() != self.meshRotation:
            self.onMeshRotationChanged()

    def setMeshScale(self):
        #print ("\nMesh Scale Set\n")
        self._sceneNode.setScale(self.meshScale)
        self._sceneNode.transformationChanged.emit(self._sceneNode)

    def onMeshScaleChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating or (self.connector.status is SmartSliceCloudStatus.BusyOptimizing):
            self.connector._confirmValidation()
            self.connector._proxy.shouldRaiseWarning = True
            print ("Mesh Scale Change Confirmed")
            self._propertiesChanged.append(SmartSliceValidationProperty.MeshScale)
            self.newScale = self._sceneNode.getScale()
        else:
            print ("\nMesh Scale Set\n")
            self.connector._prepareValidation()
            self.meshScale = self._sceneNode.getScale()

    def setMeshRotation(self):
        #print ("\nMesh Rotation Set\n")
        self._sceneNode.setOrientation(self.meshRotation)
        self._sceneNode.transformationChanged.emit(self._sceneNode)

    def onMeshRotationChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating or (self.connector.status is SmartSliceCloudStatus.BusyOptimizing):
            self._propertiesChanged.append(SmartSliceValidationProperty.MeshRotation)
            self.connector._proxy.shouldRaiseWarning = True
            self._changedValues.append(self._sceneNode.getOrientation())
            self.connector._confirmValidation()
        else:
            self.connector._prepareValidation()
            self.meshRotation = self._sceneNode.getOrientation()



    #
    #   MATERIAL CHANGES
    #
    activeMaterialChanged = pyqtSignal()

    def setMaterial(self):
       self._activeExtruder.material = self._material
       

    def _onMaterialChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating or (self.connector.status is SmartSliceCloudStatus.BusyOptimizing):
            #print("\n\nMATERIAL CHANGE CONFIRMED HERE\n\n")
            self._propertiesChanged.append(SmartSliceValidationProperty.Material)
            self._changedValues.append(self._activeExtruder.material)
            if len(self._propertiesChanged) > 2:
                print ("\nlength: " + str(len(self._propertiesChanged)) + "\n")
                self.connector._confirmValidation()
        else:
            #print("\n\nMATERIAL CHANGED HERE\n\n")
            #  TODO:  Next line is commented because there are two signals that are thrown
            #self.connector._prepareValidation()
            self._material = self._activeExtruder.material
            
    #
    #   FACE SELECTION
    #

    selectedFacesChanged = pyqtSignal() 

    def confirmFaceDraw(self, force=None):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating or (self.connector.status is SmartSliceCloudStatus.BusyOptimizing):
            self._propertiesChanged.append(SmartSliceValidationProperty.SelectedFace)
            self.connector._confirmValidation()
        else:
            self.connector._prepareValidation()
            self.updateMeshes()
            self.selectedFacesChanged.emit()

    def updateMeshes(self):
        #  ANCHOR MODE
        if self._selection_mode == 1:
            self._anchoredMesh = self._changedMesh
            self._anchoredFaces = self._changedFaces
        #  LOAD MODE
        else:
            self._loadedMesh = self._changedMesh
            self._loadedFaces = self._changedFaces



    #
    #   SIGNAL LISTENERS
    #

    # On GLOBAL Property Changed
    def _onGlobalPropertyChanged(self, key: str, property_name: str):

        if not self._cancelChanges:
            if self.connector.status is SmartSliceCloudStatus.BusyValidating or (self.connector.status is SmartSliceCloudStatus.BusyOptimizing):
                self.connector._confirmValidation()
            else:
                self.connector._prepareValidation()
                self.cacheGlobal()

        else: 
            return

    # On EXTRUDER Property Changed
    def _onExtruderPropertyChanged(self, key: str, property_name: str):
        if not self._cancelChanges:        
            if self.connector.status is SmartSliceCloudStatus.BusyValidating or (self.connector.status is SmartSliceCloudStatus.BusyOptimizing):
                #  Confirm Settings Changes
                self.connector._confirmValidation()
            else:
                self.connector._prepareValidation()
                self.cacheExtruder()
        
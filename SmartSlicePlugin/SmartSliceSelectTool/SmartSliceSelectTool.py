# Copyright (c) 2018 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.


#   Filesystem Control
import os.path

#  Ultimaker Imports
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("smartslice")

from UM.Application import Application
from UM.Version import Version
from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger
from UM.Event import Event, MouseEvent, KeyEvent

from UM.Tool import Tool

from UM.View.GL.OpenGL import OpenGL
from UM.Scene.Selection import Selection

#  QT / QML Imports
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtQml import QQmlComponent, QQmlContext # @UnresolvedImport

#  Local Imports
from .SmartSliceSelectHandle import SmartSliceSelectHandle
from .SmartSliceDrawSelection import SmartSliceSelectionVisualizer
from .FaceSelection import SelectableFace, SelectablePoint


# Provides enums
class SelectionMode:
    AnchorMode = 1
    LoadMode = 2


##  Provides the tool to rotate meshes and groups
#
#   The tool exposes a ToolHint to show the rotation angle of the current operation
class SmartSliceSelectTool(Tool):
    def __init__(self):
        super().__init__()
        #self._handle = SmartSliceSelectHandle()

        #self._shortcut_key = Qt.Key_S

        self._selection_mode = SelectionMode.AnchorMode
        self.setExposedProperties("AnchorSelectionActive",
                                  "LoadSelectionActive",
                                  "SelectionMode",
                                  )

        Selection.selectedFaceChanged.connect(self._onSelectedFaceChanged)
        self.selected_face = None

        self._controller.activeToolChanged.connect(self._onActiveStateChanged)

        #  Create new 'Selection Visualizer' with no faces actively selected
        print("\n")
        self._visualizer = SmartSliceSelectionVisualizer()
        Logger.log("d", "Enabling Selection Vizualizer")


        print("\n")


    ##  Handle mouse and keyboard events
    #
    #   \param event type(Event)
    def event(self, event):
        super().event(event)

        """
        if event.type == Event.KeyPressEvent and event.key == KeyEvent.ShiftKey:
            Logger.log("d", "Enabling faceSelectMode!")
            #Selection.setFaceSelectMode(True)
        if event.type == Event.KeyReleaseEvent and event.key == KeyEvent.ShiftKey:
            Logger.log("d", "Disabling faceSelectMode!")
            #Selection.setFaceSelectMode(False)
        """
        
        if event.type == Event.MousePressEvent:
            if MouseEvent.LeftButton not in event.buttons:
                return False

            #id = self._selection_pass.getIdAtPosition(event.x, event.y)
            #if not id:
            #    return False

            """
            if self._handle.isAxis(id):
                self.setLockedAxis(id)
            else:
                # Not clicked on an axis: do nothing.
                return False
            handle_position = self._handle.getWorldPosition()
            """

            """
            if Selection.hasSelection() and not Selection.getFaceSelectMode():
                Selection.setFaceSelectMode(True)
                Logger.log("d", "Enabled faceSelectMode!")
            elif not Selection.getSelectedFace() and Selection.getFaceSelectMode():
                Selection.setFaceSelectMode(False)
                Logger.log("d", "Disabled faceSelectMode!")
            """

            Logger.log("d", "Selection.getSelectedFace(): {}".format(Selection.getSelectedFace()))

            return True
            

        if event.type == Event.MouseReleaseEvent:
            # Finish a rotate operation
            if self.selected_face:
                '''Application.getInstance().messageBox("SmartSlice",
                                                     "You selected face: {}\ngetFaceSelectMode={}".format(self.selected_face,
                                                                                                          Selection.getFaceSelectMode()
                                                                                                          )
                                                     )'''

            return True

    def _onSelectedFaceChanged(self):
        self.selected_face = Selection.getSelectedFace()
        if self.selected_face:
            scene_node, face_id = self.selected_face
            mesh_data = scene_node.getMeshData()
            
            norms = []

            #print(dir(scene_node.getMeshData()))
            
            #if not mesh_data._indices or len(mesh_data._indices) == 0:
            if len(mesh_data._indices) == 0:
                base_index = face_id * 3
                p0 = SelectablePoint(mesh_data._vertices[base_index][0], mesh_data._vertices[base_index][1], mesh_data._vertices[base_index][2])
                p1 = SelectablePoint(mesh_data._vertices[base_index+1][0], mesh_data._vertices[base_index+1][1], mesh_data._vertices[base_index+1][2])
                p2 = SelectablePoint(mesh_data._vertices[base_index+2][0], mesh_data._vertices[base_index+2][1], mesh_data._vertices[base_index+2][2])
            else:
                p0 = SelectablePoint(mesh_data._vertices[mesh_data._indices[face_id][0]][0], mesh_data._vertices[mesh_data._indices[face_id][0]][1], mesh_data._vertices[mesh_data._indices[face_id][0]][2])
                p1 = SelectablePoint(mesh_data._vertices[mesh_data._indices[face_id][1]][0], mesh_data._vertices[mesh_data._indices[face_id][1]][1], mesh_data._vertices[mesh_data._indices[face_id][1]][2])
                p2 = SelectablePoint(mesh_data._vertices[mesh_data._indices[face_id][2]][0], mesh_data._vertices[mesh_data._indices[face_id][2]][1], mesh_data._vertices[mesh_data._indices[face_id][2]][2])
            
            #  Construct Selectable Face && Draw Selection in canvas
            sf = SelectableFace([p0, p1, p2], mesh_data._normals)
            self._visualizer.changeSelection([sf])


            '''
            print("v_a", v_a)
            print("v_b", v_b)
            print("v_c", v_c)
            '''


    def _onActiveStateChanged(self):
        active_tool = Application.getInstance().getController().getActiveTool()
        Logger.log("d", "Application.getInstance().getController().getActiveTool(): {}".format(Application.getInstance().getController().getActiveTool()))

        if active_tool == self and Selection.hasSelection():
            Selection.setFaceSelectMode(True)
            Logger.log("d", "Enabled faceSelectMode!")
        else:
            Selection.setFaceSelectMode(False)
            Logger.log("d", "Disabled faceSelectMode!")

    ##  Get whether the select face feature is supported.
    #   \return True if it is supported, or False otherwise.
    def getSelectFaceSupported(self) -> bool:
        # Use a dummy postfix, since an equal version with a postfix is considered smaller normally.
        return Version(OpenGL.getInstance().getOpenGLVersion()) >= Version("4.1 dummy-postfix")
    
    def setSelectionMode(self, mode):
        if self._selection_mode is not mode:
            self._selection_mode = mode
            
            Logger.log("d", "Changed selection mode to enum: {}".format(mode))

    def getSelectionMode(self):
        return self._selection_mode

    def setAnchorSelection(self):
        self.setSelectionMode(SelectionMode.AnchorMode)

    def getAnchorSelectionActive(self):
        return self._selection_mode is SelectionMode.AnchorMode

    def setLoadSelection(self):
        self.setSelectionMode(SelectionMode.LoadMode)

    def getLoadSelectionActive(self):
        return self._selection_mode is SelectionMode.LoadMode

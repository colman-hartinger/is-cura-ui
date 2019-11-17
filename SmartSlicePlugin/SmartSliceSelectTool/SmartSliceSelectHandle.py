# SmartSliceSelectHandle.py
# Teton Simulation
# Last Modified November 12, 2019

# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

#
#   Contains functionality to be triggered upon face selection
#


#  UM/Cura Imports
from UM.Logger import Logger
from UM.Scene.ToolHandle import ToolHandle
from UM.Scene.SceneNode import SceneNode
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Mesh.MeshData import MeshData

from UM.Math.Color import Color
from UM.Math.Matrix import Matrix
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector

# Local Imports
from .FaceSelection import SelectableFace
from .FaceSelection import toCalculatableFace
from .Detessellate import isCoplanar, isJointed
from .SmartSliceSelectionProxy import SmartSliceSelectionConnector


# Provides enums
class SelectionMode:
    AnchorMode = 1
    LoadMode = 2

class SmartSliceSelectHandle(ToolHandle):
#  CONSTRUCTORS
    def __init__(self, parent = None, tri: SelectableFace = None):
        super().__init__(parent)

        self._name = "SmartSliceSelectHandle"
        self._connector = SmartSliceSelectionConnector()

        #  Default Line Properties
        self._edge_width = 0.8
        self._edge_length = [] # TODO: GET THIS FROM FACE EDGES
        self._selected_color = self.AllAxisSelectionColor
        self._anchored_color = self._y_axis_color
        self._loaded_color = self._y_axis_color

        #  Selected Face Properties
        self._tri = tri
        self._face = []
        self._center = self.findCenter()

        #  Previously Selected Faces
        self._loaded_faces = set()
        self._load_magnitude = 0
        self._anchored_faces = set()

        #   Arrow Mesh
        self._arrow = None
        
        #  Disable auto scale
        self._auto_scale = False



#  ACCESSORS
    @property
    def face(self):
        return self._tri

#  MUTATORS
    def setFace(self, f):
        self._tri = f
        self._center = self.findCenter()

    def getLoadVector(self):
        if len(self._loaded_faces) > 0:
            load_mag = self._connector._proxy._loadMagnitude
            lf = toCalculatableFace(list(self._loaded_faces)[0])
            n = lf.normal
            return Vector(load_mag*n.x, load_mag*n.y, load_mag*n.z)
        return Vector(0., 0., 0.) # no load face available to determine vector


    '''
      drawFaceSelection()

        Uses UM's MeshBuilder to construct 3D Arrow mesh and translates/rotates as to be normal to the selected face
    '''
    def drawFaceSelection(self, mode, draw_arrow = False, other_faces = []):
        #  Construct Edges using MeshBuilder Cubes
        mb = MeshBuilder()

        Logger.log("d", "Root Face: {}".format(self._tri))

        f = self._tri
        self._face = set()

        if mode == SelectionMode.LoadMode:
            self._load_magnitude = 10 # is this being used??

        #if draw_arrow:
        #    self.drawNormalArrow()
        #    self.addChild(self._arrow)

        coplanar_faces = set((f,))
        possible_faces = set()
        checked = set()

        for _tri in other_faces:
            if _tri in checked:
                continue

            checked.add(_tri)

            #Logger.log('d', '{} ->\n{}\n {}'.format(f, _tri, f.normal.angleToVector(_tri.normal)))

            if isCoplanar(f, _tri):
                possible_faces.add(_tri)
                
                #  Paint Faces that are recursively coplanar/jointed
                # TODO Brady - commented out
                #self.paintPossibleFaces(mode, mb, _tri, checked)

        # now filter possible faces into faces that are only connected to the root face
        faces_added = 1
        while faces_added > 0:
            connected = set()
            for f1 in possible_faces:
                for f2 in coplanar_faces:
                    if isJointed(f1, f2):
                        connected.add(f1)
            faces_added = len(connected)
            for f in connected:
                coplanar_faces.add(f)
                possible_faces.remove(f)

        for _tri in coplanar_faces:
            self.paintFace(_tri, mb)

        if mode == SelectionMode.LoadMode:
            self._loaded_faces = coplanar_faces
        else:
            self._anchored_faces = coplanar_faces

        #  Add to Cura Scene
        self.setSolidMesh(mb.build())

        Logger.log("d", "Anchor Faces: {}".format([f._id for f in self._anchored_faces]))
        Logger.log("d", "Load Faces: {}".format([f._id for f in self._loaded_faces]))
        Logger.log("d", "Load Vector: {}".format(self.getLoadVector()))
        
        lv = self.getLoadVector()
        print ("NORMAL FORCE: (" + str(lv.x) + ", " + str(lv.y) + ", " + str(lv.z) + ")")


    '''
      paintFace(tri, mb)
        tri: SelectableFace (EXACTLY 3 Vertices)
        mb: MeshBuilder

        Creates a face representitive of 'tri' within mb and paints it selected color
    '''
    def paintFace(self, tri, mb):
        p = tri.points
        tri.generateNormalVector()
        n = tri.normal
        p0 = Vector(p[0].x, p[0].y, p[0].z)
        p1 = Vector(p[1].x, p[1].y, p[1].z)
        p2 = Vector(p[2].x, p[2].y, p[2].z)
        norm = Vector(n.x, n.y, n.z)
        mb.addFace(p0, p1, p2, n, self._selected_color)

    '''
      paintPossibleFaces(mb, face, possible)
        mb: MeshBuilder
        face: SelectableFace
        possible: List of SelectableFaces

        Paints all SelectableFaces in 'possible' that are jointed/coplanar with 'face'
        NOTE:  This assumes all entries in 'possible' are coplanar with 'face'
    '''
    def paintPossibleFaces(self, mode, mb, face, possible : set):
        for _tri in possible:
            if isJointed(face, _tri):
                self.paintFace(_tri, mb)
                self._face.add(_tri)
                possible.remove(_tri)
                self.paintPossibleFaces(mode, mb, _tri, possible)
                if mode == SelectionMode.LoadMode:
                    self._loaded_faces.add(_tri)
                else:
                    self._anchored_faces.add(_tri)

    '''
      paintAnchoredFaces()

        Repaints the saved selection for applied Anchors
    '''
    def paintAnchoredFaces(self):
        mb = MeshBuilder()
        for _tri in self._anchored_faces:
            self.paintFace(_tri, mb)
        #  Add to Cura Scene
        self.setSolidMesh(mb.build())  

    '''
      paintLoadedFaces()

        Repaints the saved selection for applied Loads
    '''
    def paintLoadedFaces(self):
        mb = MeshBuilder()
        for _tri in self._loaded_faces:
            self.paintFace(_tri, mb)
        #  Add to Cura Scene
        self.setSolidMesh(mb.build())  


    '''
      drawNormalArrow()
    '''
    def drawNormalArrow(self):
        mb = MeshBuilder()
        if self._arrow is not None:
            self.removeChild(self._arrow)
        self._arrow = SceneNode(self, name="_NormalArrow")

        f = self._tri
        n = f.generateNormalVector()

        #  Paint Normal Arrow
        center_shaft = Vector(self._center[0], self._center[1]+5, self._center[2])
        center_head = Vector(self._center[0], self._center[1]+10, self._center[2])

        mb.addCube(1, 10, 1, center_shaft, self._color)
        mb.addPyramid(5, 5, 5, 0, Vector.Unit_Y, center_head, self._color)
        
        '''
        mat = Matrix()
        mat.setByRotationAxis(180*n.x, Vector.Unit_X)
        mat.setByRotationAxis(-180*(1-n.y), Vector.Unit_Y)
        mat.setByRotationAxis(180*n.z, Vector.Unit_Z)
        self._arrow.rotate(Quaternion().fromMatrix(mat))
        '''

        #  Add to Cura Scene
        self._arrow.setMeshData(mb.build())

    '''
      findCenter()

        calculates center vector for currently selected face
    '''
    def findCenter(self):
        i = 0
        x = 0.
        y = 0.
        z = 0.

        if self._tri is None:
            return [0, 0, 0]

        for p in self._tri.points:
            
            x += p.x
            y += p.y
            z += p.z
            
            i += 1

        return [x/i, y/i, z/i]


    def clearSelection(self):
        mb = MeshBuilder()
        self.setSolidMesh(mb.build())  

    def _onEngineCreated(self):
        self._connector._onEngineCreated()
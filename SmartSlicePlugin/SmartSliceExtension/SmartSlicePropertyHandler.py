#   SmartSlicePropertyHandler.py
#   Teton Simulation
#   Authored on   January 3, 2019
#   Last Modified January 3, 2019

#
#  Contains procedures for handling Cura Properties in accordance with SmartSlice
#


from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtProperty
from PyQt5.QtCore import QObject

#  Cura
from UM.Application import Application
from cura.CuraApplication import CuraApplication

#  Smart Slice
from .SmartSliceCloudProxy import SmartSliceCloudStatus
from .SmartSliceValidationProperty import SmartSliceValidationProperty

class SmartSlicePropertyHandler(QObject):
    def __init__(self, connector):
        super().__init__()

        #  Callback
        self.connector = connector
        
        self._activeMachineManager = CuraApplication.getInstance().getMachineManager()
        self._activeExtruder = self._activeMachineManager._global_container_stack.extruderList[0]
        global_stack = Application.getInstance().getGlobalContainerStack()
        
        #  Connect Signals
        global_stack.propertyChanged.connect(self._onGlobalPropertyChanged)
        self._activeExtruder.propertyChanged.connect(self._onExtruderPropertyChanged)
        self._activeMachineManager.activeMaterialChanged.connect(self._onMaterialChanged)
        
        #  Cache Space
        self._propertyChanged = None
        self._changedValue = None
        self._changedFloat = None
        self._changedBool  = None
        self._changedString = None

        #
        #   DEFAULT PROPERTY VALUES
        #

        #  Shell
        self.wallThickness = self._activeExtruder.getProperty("wall_thickness", "value")
        self.wallLineCount = self._activeExtruder.getProperty("wall_line_count", "value")
        self.topThickness = self._activeExtruder.getProperty("top_thickness", "value")
        self.topLayers = self._activeExtruder.getProperty("top_layers", "value")
        self.bottomLayers = self._activeExtruder.getProperty("bottom_layers", "value")
        self.bottomThickness = self._activeExtruder.getProperty("bottom_thickness", "value")
        self.horizontalExpansion = None
        self.alternateExtraWall = self._activeExtruder.getProperty("alternate_extra_perimeter", "value")
        self.skinAngles = self._activeExtruder.getProperty("skin_angles", "value")

        #  Line Widths / Layering
        self.layerHeight = self._activeExtruder.getProperty("layer_height", "value")
        self.layerHeightInitial = self._activeExtruder.getProperty("layer_height_0", "value")
        self.lineWidth = self._activeExtruder.getProperty("line_width", "value")
        self.lineWidthInitialLayer = self._activeExtruder.getProperty("line_width_0", "value")
        self.lineWidthWall = self._activeExtruder.getProperty("wall_line_width", "value")
        self.lineWidthOuter = self._activeExtruder.getProperty("wall_line_width_0", "value")
        self.lineWidthInner = self._activeExtruder.getProperty("wall_line_width_x", "value")
        self.lineWidthTopBottom = None
        self.lineWidthInfill = self._activeExtruder.getProperty("infill_line_width", "value")

        #  Infills
        self.infillDensity = self._activeExtruder.getProperty("infill_sparse_density", "value")
        self.infillLineDistance = self._activeExtruder.getProperty("infill_line_distance", "value")
        self.infillPattern = self._activeExtruder.getProperty("infill_pattern", "value")
        self.infillLineDirection = self._activeExtruder.getProperty("infill_angles", "value")
        self.infillOffsetX = self._activeExtruder.getProperty("infill_offset_x", "value")
        self.infillOffsetY = self._activeExtruder.getProperty("infill_offset_y", "value")
        self.infillMultiplier = self._activeExtruder.getProperty("infill_multiplier", "value")
        self.infillOverlapPercentage = self._activeExtruder.getProperty("infill_overlap_percentage", "value")
        self.infillOverlapMM = self._activeExtruder.getProperty("infill_overlap_mm", "value")

        


        self._material = None #  Cura Material Node

        #  UI/Validation Signals
        self.activeMaterialChanged.connect(self._onMaterialChanged)

        
    #
    #   QUALITY PROPERTIES
    #


    #
    #   SHELL PROPERTIES
    #

    #  Alternate Extra Wall (DISFUNCT)
    def setAlternateExtraWall(self):
        self._activeExtruder.setProperty("alternate_extra_perimeter", "value", self.alternateExtraWall)

    def onAlternateExtraWallChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.AlternateExtraWall
            self._changedBool = self._activeExtruder.getProperty("alternate_extra_perimeter", "value")
            self.connector._confirmValidation()
        else:
            self.alternateExtraWall = self._activeExtruder.getProperty("alternate_extra_perimeter", "value")

    #  Top/Bottom Line Directions (DISFUNCT)
    def setSkinAngles(self):
        self._activeExtruder.setProperty("skin_angles", "value", self.skinAngles)

    def onSkinAnglesChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.SkinAngles
            self._changedString = self._activeExtruder.getProperty("skin_angles", "value")
            self.connector._confirmValidation()
        else:
            self.skinAngles = self._activeExtruder.getProperty("skin_angles", "value")

    #
    #   SHELL PROPERTIES
    #

    def setLayerHeight(self):
        self._activeMachineManager._global_container_stack.setProperty("layer_height", "value", self.layerHeight)

    def onLayerHeightChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.LayerHeight
            self._changedFloat = self._activeMachineManager._global_container_stack.getProperty("layer_height", "value")
            self.connector._confirmValidation()
        else:
            self.layerHeight = self._activeMachineManager._global_container_stack.getProperty("layer_height", "value")

    def setInitialLayerHeight(self):
        self._activeExtruder.setProperty("initial_layer_height", "value", self.layerHeightInitial)

    def onInitialLayerHeightChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InitialLayerHeight
            self._changedFloat = self._activeExtruder.getProperty("initial_layer_height", "value")
            self.connector._confirmValidation()
        else:
            self.layerHeightInitial = self._activeExtruder.getProperty("initial_layer_height", "value")

    def onInitialLayerLineWidthChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InitialLayerLineWidth
            self._changedValue = self._activeExtruder.getProperty("initial_layer_line_width", "value")
            self.connector._confirmValidation()
        else:
            self.lineWidthInitialLayer = self._activeExtruder.getProperty("initial_layer_line_width", "value")


    def setLineWidth(self):
        self._activeExtruder.setProperty("line_width", "value", self.lineWidth)

    def onLineWidthChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.LineWidth
            self._changedFloat = self._activeExtruder.getProperty("line_width", "value")
            self.connector._confirmValidation()
        else:
            self.lineWidth = self._activeExtruder.getProperty("line_width", "value")

    def setWallLineWidth(self):
        self._activeExtruder.setProperty("wall_line_width", "value", self.lineWidthWall)

    def onWallLineWidthChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.WallLineWidth
            self._changedFloat = self._activeExtruder.getProperty("wall_line_width", "value")
            self.connector._confirmValidation()
        else:
            self.lineWidth = self._activeExtruder.getProperty("wall_line_width", "value")
        

    def setOuterLineWidth(self):
        self._activeExtruder.setProperty("wall_line_width_0", "value", self.lineWidthOuter)

    def onOuterLineWidthChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.OuterLineWidth
            self._changedFloat = self._activeExtruder.getProperty("wall_line_width_0", "value")
            self.connector._confirmValidation()
        else:
            self.lineWidthOuter = self._activeExtruder.getProperty("wall_line_width_0", "value")

    def setInnerLineWidth(self):
        self._activeExtruder.setProperty("wall_line_width_x", "value", self.lineWidthInner)

    def onInnerLineWidthChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InnerLineWidth
            self._changedFloat = self._activeExtruder.getProperty("wall_line_width_x", "value")
            self.connector._confirmValidation()
        else:
            self.lineWidthInner = self._activeExtruder.getProperty("wall_line_width_x", "value")

    def setInfillLineWidth(self):
        self._activeExtruder.setProperty("infill_line_width", "value", self.lineWidthInfill)

    def onInfillLineWidthChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillLineWidth
            self._changedFloat = self._activeExtruder.getProperty("infill_line_width", "value")
            self.connector._confirmValidation()
        else:
            self.lineWidthInfill = self._activeExtruder.getProperty("infill_line_width", "value")


    def setWallThickness(self):
        self._activeExtruder.setProperty("wall_thickness", "value", self.wallThickness)

    def onWallThicknessChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.WallThickness
            self._changedValue = self._activeExtruder.getProperty("wall_thickness", "value")
            self.connector._confirmValidation()
        else:
            self.wallThickness = self._activeExtruder.getProperty("wall_thickness", "value")

    def setWallLineCount(self):
        self._activeExtruder.setProperty("wall_line_count", "value", self.wallLineCount)

    def onWallLineCountChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.WallLineCount
            self._changedValue = self._activeExtruder.getProperty("wall_line_count", "value")
            self.connector._confirmValidation()
        else:
            self.wallLineCount = self._activeExtruder.getProperty("wall_line_count", "value")


    #  Top Thickness
    def setTopThickness(self):
        self._activeExtruder.setProperty("top_thickness", "value", self.topThickness)

    def onTopThicknessChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.TopThickness
            self._changedValue = self._activeExtruder.getProperty("top_thickness", "value")
            self.connector._confirmValidation()
        else:
            self.topThickness = self._activeExtruder.getProperty("top_thickness", "value")

    #  Top Layers
    def setTopLayers(self):
        self._activeExtruder.setProperty("top_layers", "value", self.topLayers)

    def onTopLayersChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.TopLayers
            self._changedValue = self._activeExtruder.getProperty("top_layers", "value")
            self.connector._confirmValidation()
        else:
            self.topLayers = self._activeExtruder.getProperty("top_layers", "value")

    #  Bottom Thickness
    def setBottomThickness(self):
        self._activeExtruder.setProperty("bottom_thickness", "value",self.bottomThickness)

    def onBottomThicknessChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.BottomThickness
            self._changedValue = self._activeExtruder.getProperty("bottom_thickness", "value")
            self.connector._confirmValidation()
        else:
            self.bottomThickness = self._activeExtruder.getProperty("bottom_thickness", "value")
        
    #  Bottom Layers
    def setBottomLayers(self):
        self._activeExtruder.setProperty("bottom_layers", "value", self.bottomLayers)

    def onBottomLayersChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.BottomLayers
            self._changedValue = self._activeExtruder.getProperty("bottom_layers", "value")
            self.connector._confirmValidation()
        else:
            self.bottomLayers = self._activeExtruder.getProperty("bottom_layers", "value")

    #  Horizontal Expansion
    def setHorizontalExpansion(self):
        self._activeExtruder.setProperty("horizontal_expansion", "value", self.horizontalExpansion)

    def onHorizontalExpansionChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.HorizontalExpansion
            self._changedValue = self._activeExtruder.getProperty("horizontal_expansion", "value")
            self.connector._confirmValidation()
        else:
            self.horizontalExpansion = self._activeExtruder.getProperty("horizontal_expansion", "value")
    

    #
    #   INFILL PROPERTIES
    #

    #  Infill Line Distance
    def setInfillLineDistance(self):
        self._activeExtruder.setProperty("infill_line_distance", "value", self.infillLineDistance)

    def onInfillLineDistanceChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillLineDistance
            self._changedFloat = self._activeExtruder.getProperty("infill_line_distance", "value")
            self.connector._confirmValidation()
        else:
            self.infillLineDistance = self._activeExtruder.getProperty("infill_line_distance", "value")

    #  Infill Angles
    def setInfillAngles(self):
        self._activeExtruder.setProperty("infill_angles", "value", self.infillLineDirection)

    def onInfillAnglesChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillAngles
            self._changedString = self._activeExtruder.getProperty("infill_angles", "value")
            self.connector._confirmValidation()
        else:
            self.infillLineDirection = self._activeExtruder.getProperty("infill_angles", "value")

    def setInfillDensity(self):
        self._activeExtruder.setProperty("infill_sparse_density", "value", self.infillDensity)

    def onInfillDensityChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillDensity
            self._changedValue = self._activeExtruder.getProperty("infill_sparse_density", "value")
            self.connector._confirmValidation()
        else:
            self.infillDensity = self._activeExtruder.getProperty("infill_sparse_density", "value")

    def setInfillPattern(self):
        self._activeExtruder.setProperty("infill_pattern", "value", self.infillPattern)

    def onInfillPatternChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillPattern
            self._changedString = self._activeExtruder.getProperty("infill_pattern", "value")
            self.connector._confirmValidation()
        else:
            self.infillPattern = self._activeExtruder.getProperty("infill_pattern", "value")

    def setInfillOffsetX(self):
        self._activeExtruder.setProperty("infill_offset_x", "value", self.infillOffsetX)

    def onInfillOffsetXChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillOffsetX
            self._changedValue = self._activeExtruder.getProperty("infill_offset_x", "value")
            self.connector._confirmValidation()
        else:
            self.infillOffsetX = self._activeExtruder.getProperty("infill_offset_x", "value")

    def setInfillOffsetY(self):
        self._activeExtruder.setProperty("infill_offset_y", "value", self.infillOffsetY)

    def onInfillOffsetYChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillOffsetY
            self._changedValue = self._activeExtruder.getProperty("infill_offset_y", "value")
            self.connector._confirmValidation()
        else:
            self.infillOffsetY = self._activeExtruder.getProperty("infill_offset_y", "value")

    def setInfillMultiplier(self):
        self._activeExtruder.setProperty("infill_muliplier", "value", self.infillMultiplier)

    def onInfillMultiplierChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillLineMultiplier
            self._changedValue = self._activeExtruder.getProperty("infill_multiplier", "value")
            self.connector._confirmValidation()
        else:
            self.infillMultiplier = self._activeExtruder.getProperty("infill_multiplier", "value")

    def setInfillOverlap(self):
        self._activeExtruder.setProperty("infill_overlap", "value", self.infillOverlapPercentage)

    def onInfillOverlapChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillOverlapPer
            self._changedValue =self._activeExtruder.getProperty("infill_overlap", "value")
            self.connector._confirmValidation()
        else:
            self.infillOverlapPercentage = self._activeExtruder.getProperty("infill_overlap", "value")

    def setInfillOverlapMM(self):
        self._activeExtruder.setProperty("infill_overlap_mm", "value", self.infillOverlapMM)

    def onInfillOverlapMMChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating:
            self._propertyChanged = SmartSliceValidationProperty.InfillOverlapMM
            self._changedFloat = self._activeExtruder.getProperty("infill_overlap_mm", "value")
            self.connector._confirmValidation()
        else:
            self.infillOverlapMM = self._activeExtruder.getProperty("infill_overlap_mm")


        

    def onTopLineDirectionChanged(self):
        #  STUB 
        1 + 1

    def onBottomLineDirectionChanged(self):
        #  STUB 
        1 + 1

    def onMeshScaleChangd(self):
        #  STUB
        1 + 1

    def onMeshRotationChanged(self):
        #  STUB 
        1 + 1

    #
    #   MATERIAL CHANGES
    #
    activeMaterialChanged = pyqtSignal()

    def setMaterial(self):
       self._activeExtruder.material = self._material

    def _onMaterialChanged(self):
        if self.connector.status is SmartSliceCloudStatus.BusyValidating and (self._material != None):
            #print("\n\nMATERIAL CHANGE CONFIRMED HERE\n\n")
            self._propertyChanged = SmartSliceValidationProperty.Material
            self._changedMaterial = self._activeMachineManager._global_container_stack.extruderList[0].material
            #self.connector._confirmValidation()
        else:
            #print("\n\nMATERIAL CHANGED HERE\n\n")
            self._material = self._activeMachineManager._global_container_stack.extruderList[0].material
            self.setMaterial()


    #
    #   PROPERTY CHANGES
    #

    # On GLOBAL Property Changed
    def _onGlobalPropertyChanged(self, key: str, property_name: str):

        if   key == "layer_height" and property_name == "value":          
            self.onLayerHeightChanged()
        elif key == "initial_layer_height" and property_name == "value":   
            self.onInitialLayerHeightChanged()

        else: 
            return

    # On EXTRUDER Property Changed
    def _onExtruderPropertyChanged(self, key: str, property_name: str):
        
        if   key == "infill_sparse_density" and property_name == "value":
            self.onInfillDensityChanged()
        elif key == "infill_line_distance" and property_name == "value":
            self.onInfillLineDistanceChanged()
        elif key == "infill_pattern" and property_name == "value":
            self.onInfillPatternChanged()
        elif key == "infill_multiplier" and property_name == "value":
            self.onInfillMultiplierChanged()
        elif key == "infill_offset_x" and property_name == "value":
            self.onInfillOffsetXChanged()
        elif key == "infill_offset_y" and property_name == "value":
            self.onInfillOffsetYChanged()
        elif key == "infill_overlap" and property_name == "value":
            self.onInfillOverlapChanged()
        elif key == "infill_overlap_mm" and property_name == "value":
            self.onInfillOverlapMMChanged()
        
        elif key == "line_width" and property_name == "value":
            self.onLineWidthChanged()
        elif key == "wall_line_width" and property_name == "value":
            self.onOuterLineWidthChanged()
        elif key == "wall_line_width" and property_name == "value":
            self.onInnerLineWidthChanged()
        elif key == "infill_wall_line_width" and property_name == "value":
            self.onInfillLineWidthChanged()
        elif key == "wall_thickness" and property_name == "value":
            self.onWallThicknessChanged()
        elif key == "wall_line_count" and property_name == "value":
            self.onWallLineCountChanged()
        elif key == "horizontal_expansion" and property_name == "value":    # DISFUNCT!!!!
            self.onHorizontalExpansionChanged()
        
        elif key == "top_thickness" and property_name == "value":
            self.onTopThicknessChanged()
        elif key == "top_layers" and property_name == "value":
            self.onTopLayersChanged()
        elif key == "bottom_thickness" and property_name == "value":
            self.onBottomThicknessChanged()
        elif key == "bottom_layers" and property_name == "value":
            self.onBottomLayersChanged()

        #  Invalid Property
        else:
            return

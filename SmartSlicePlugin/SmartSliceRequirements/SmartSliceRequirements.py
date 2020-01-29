#   SmartSliceRequirements.py
#   Teton Simulation
#   Authored on   October 8, 2019
#   Last Modified October 8, 2019

#
#   Contains definitions for the "Requirements" Tool, which serves as an interface for requirements
#
#   Types of Requirements:
#     * Safety Factor
#     * Maximum Deflection
#

#   Ultimaker/Cura Imports
from UM.Application import Application
from UM.Tool import Tool
from UM.PluginRegistry import PluginRegistry

from .SmartSliceValidationProperty import SmartSliceValidationProperty

#   Smart Slice Requirements Tool:
#     When Pressed, this tool produces the "Requirements Dialog"
#
class SmartSliceRequirements(Tool):
    #  Class Initialization
    def __init__(self):
        super().__init__()

        self._connector = PluginRegistry.getInstance().getPluginObject("SmartSliceExtension").cloud

        self._controller.activeToolChanged.connect(self._onToolSelected)

    def _onToolSelected(self):
        if not self._connector._proxy.shouldRaiseWarning:
            print ("TRIGGERED REQUIREMENTS TOOL!!")
            self._connector._proxy.confirmationWindowEnabled = False
            self._connector._proxy.confirmationWindowEnabledChanged.emit()
            
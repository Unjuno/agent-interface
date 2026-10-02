import unittest
from research.live_control import compiled_gui_interface_v1
from runtime.core_v1 import compiled_gui

class CompiledCompatibilityTests(unittest.TestCase):
    def test_compatibility_entry_is_the_shared_implementation(self):
        self.assertIs(compiled_gui_interface_v1.run, compiled_gui.run)
        self.assertIs(compiled_gui_interface_v1.validate, compiled_gui.validate)

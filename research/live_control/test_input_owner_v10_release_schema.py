"""Verify V10's successful release record matches the cleanup audit schema."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent


class FakeRoot:
    def query_pointer(self):
        return types.SimpleNamespace(mask=0)


class FakeDisplay:
    def __init__(self, _display_name):
        self.root = FakeRoot()

    def sync(self):
        pass

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        return bytes(32)


def load_input_owner_v10_without_x11():
    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace()
    xlib.XK = types.SimpleNamespace()
    xlib.display = types.SimpleNamespace(Display=FakeDisplay)
    xlib.error = types.SimpleNamespace()
    xlib_ext = types.ModuleType("Xlib.ext")
    xlib_ext.xtest = types.SimpleNamespace()
    with patch.dict(sys.modules, {"Xlib": xlib, "Xlib.ext": xlib_ext}):
        spec = importlib.util.spec_from_file_location(
            "_v10_release_schema_under_test", HERE / "input_owner_v10.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.InputOwner


class InputOwnerV10ReleaseSchemaTests(unittest.TestCase):
    def test_successful_release_records_known_empty_key_state(self):
        owner_type = load_input_owner_v10_without_x11()
        owner = owner_type("fake-display")
        try:
            record = owner.call("release")
        finally:
            owner.close()

        self.assertIs(record["verified"], True)
        self.assertEqual(record["keys_down"], [])
        self.assertEqual(record["buttons_down"], [])
        self.assertEqual(record["keys_unknown"], [])
        self.assertEqual(record["key_state_errors"], [])


if __name__ == "__main__":
    unittest.main()

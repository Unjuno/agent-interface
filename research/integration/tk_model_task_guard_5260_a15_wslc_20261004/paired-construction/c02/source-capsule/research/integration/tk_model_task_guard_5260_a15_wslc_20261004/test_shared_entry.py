"""Construction qualification against actual shared imports, no model or input."""
import importlib
import tempfile
import unittest


class SharedEntryConstructionTests(unittest.TestCase):
    def entry(self):
        try:
            return importlib.import_module('runtime.cli_v1.mcp_guarded').GuardedSessionOwner
        except ImportError as error:
            self.fail('Actual shared entry dependencies unavailable: ' + str(error))

    def test_empty_target_configuration_denied_before_open(self):
        owner_type = self.entry()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                owner_type({}, directory, display_name=':97')

    def test_unopened_owner_cannot_grant_input_guard(self):
        owner_type = self.entry()
        with tempfile.TemporaryDirectory() as directory:
            owner = owner_type({'app': 101}, directory, display_name=':97')
            with self.assertRaises(RuntimeError):
                with owner.input_guard('entry', [0, 0],
                                       tail=[{'op': 'text', 'text': 'q'}],
                                       verify=lambda *args: True):
                    self.fail('Unopened guard unexpectedly entered')
            self.assertEqual(owner.state, 'unopened')
            self.assertIsNone(owner.bridge)
            self.assertFalse(owner.close()['release_attempted'])

    def test_native_bridge_dependency_imports_without_connection(self):
        try:
            module = importlib.import_module('runtime.guarded_x11_v1.bridge')
        except ImportError as error:
            self.fail('Actual native bridge dependencies unavailable: ' + str(error))
        self.assertTrue(callable(module.NativeHandleBridge))


if __name__ == '__main__':
    unittest.main()

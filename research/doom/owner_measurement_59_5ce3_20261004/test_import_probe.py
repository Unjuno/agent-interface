"""Real file-import construction tests; no native environment or game."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


class ImportProbeTests(unittest.TestCase):
    def probe(self):
        path = Path(__file__).with_name('probe_imports.py')
        self.assertTrue(path.is_file(), 'missing real import probe')
        spec = importlib.util.spec_from_file_location('import_probe_under_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_real_file_import_does_not_call_script_main(self):
        probe = self.probe()
        name = 'owner_measurement_test_import_5ce3'
        self.addCleanup(sys.modules.pop, name, None)
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'fixture.py'
            source.write_text('import math\nvalue = math.factorial(5)\n'
                              'if __name__ == "__main__":\n    raise RuntimeError("main called")\n')
            module = probe.load_file(name, source)
            self.assertEqual(module.value, 120)
            self.assertIs(sys.modules[name], module)
            with self.assertRaises(ValueError):
                probe.load_file(name, source)

    def test_failed_import_does_not_leave_partial_module_registered(self):
        probe = self.probe()
        name = 'owner_measurement_failed_import_5ce3'
        self.addCleanup(sys.modules.pop, name, None)
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'fixture.py'
            source.write_text('raise ValueError("import failed")\n')
            with self.assertRaises(ValueError):
                probe.load_file(name, source)
            self.assertNotIn(name, sys.modules)


if __name__ == '__main__':
    unittest.main()

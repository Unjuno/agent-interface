import os
import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_call_backend_v1 import resolve


class BackendSeamTest(unittest.TestCase):
    def tearDown(self):
        for name in ("AGENT_INTERFACE_MODEL_BACKEND",
                     "AGENT_INTERFACE_MODEL_CALL_MODULE"):
            os.environ.pop(name, None)
        sys.modules.pop("test_backend_module", None)

    def test_legacy_is_default(self):
        sentinel = object()
        self.assertIs(resolve(sentinel), sentinel)

    def test_unconfigured_module_stops(self):
        os.environ["AGENT_INTERFACE_MODEL_BACKEND"] = "module"
        with self.assertRaisesRegex(RuntimeError, "STOP_MODEL_BACKEND_UNCONFIGURED"):
            resolve(lambda: None)

    def test_explicit_module_is_selected(self):
        module = types.ModuleType("test_backend_module")
        module.call = lambda *args, **kwargs: "selected"
        sys.modules[module.__name__] = module
        os.environ["AGENT_INTERFACE_MODEL_BACKEND"] = "module"
        os.environ["AGENT_INTERFACE_MODEL_CALL_MODULE"] = module.__name__
        self.assertEqual(resolve(lambda: "legacy")(), "selected")

    def test_unknown_backend_stops(self):
        os.environ["AGENT_INTERFACE_MODEL_BACKEND"] = "unknown"
        with self.assertRaisesRegex(RuntimeError, "STOP_MODEL_BACKEND_UNSUPPORTED"):
            resolve(lambda: None)


if __name__ == "__main__":
    unittest.main()
import os
import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_call_backend_v1 import (resolve, resolve_preflight_call,
                                   resolve_preflight_identity)


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

    def test_legacy_preflight_transport_and_identity_are_defaults(self):
        call = object()
        identity = object()
        self.assertIs(resolve_preflight_call(call), call)
        self.assertIs(resolve_preflight_identity(identity), identity)

    def test_module_backend_must_implement_both_preflight_contracts(self):
        module = types.ModuleType("test_backend_module")
        module.call = lambda *args, **kwargs: "selected"
        module.preflight_call = lambda *args, **kwargs: "preflight"
        module.preflight_identity = lambda schema: ({"schema": str(schema)}, "key")
        sys.modules[module.__name__] = module
        os.environ["AGENT_INTERFACE_MODEL_BACKEND"] = "module"
        os.environ["AGENT_INTERFACE_MODEL_CALL_MODULE"] = module.__name__
        self.assertIs(resolve_preflight_call(lambda: None), module.preflight_call)
        self.assertIs(resolve_preflight_identity(lambda: None), module.preflight_identity)

        del module.preflight_call
        with self.assertRaisesRegex(RuntimeError, "STOP_MODEL_BACKEND_MISSING_PREFLIGHT_CALL"):
            resolve_preflight_call(lambda: None)
        del module.preflight_identity
        with self.assertRaisesRegex(RuntimeError, "STOP_MODEL_BACKEND_MISSING_PREFLIGHT_IDENTITY"):
            resolve_preflight_identity(lambda: None)


if __name__ == "__main__":
    unittest.main()

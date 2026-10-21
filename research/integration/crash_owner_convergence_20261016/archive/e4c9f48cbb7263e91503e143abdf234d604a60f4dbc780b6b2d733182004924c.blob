"""Composition contract for the opt-in V15 process-owned backend."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name(
    "doom_owner_thread_release_batch_backend_process_v1.py")


class PreviousBackend:
    def __init__(self, session, out, emit, signal_readers):
        self.owner = types.SimpleNamespace(closed=False, close=lambda: setattr(
            self.owner, "closed", True))


class ProcessBackendCompositionTests(unittest.TestCase):
    def test_replaces_empty_local_owner_and_publishes_exact_service_identity(self):
        base = types.ModuleType("doom_owner_thread_release_batch_backend_v1")
        base.Backend = PreviousBackend
        process_module = types.ModuleType("input_owner_process_v1")
        instances = []

        class FakeProcessOwner:
            def __init__(self, display, out):
                self.owner_id = "owner-7"
                self.service_pid = 45678
                self.service_start_ticks = 98765
                self.receipt_path = Path(out) / "input-owner-recovery-v1.json"
                self.calls = []
                instances.append((display, Path(out), self))

            def close(self):
                self.calls.append("close")
                return "closed"

        process_module.InputOwnerProcess = FakeProcessOwner
        old_base = sys.modules.get(base.__name__)
        old_process = sys.modules.get(process_module.__name__)
        sys.modules[base.__name__] = base
        sys.modules[process_module.__name__] = process_module
        try:
            spec = importlib.util.spec_from_file_location(
                "process_backend_under_test", SOURCE)
            candidate = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(candidate)
            events = []
            with tempfile.TemporaryDirectory() as temp:
                backend = candidate.Backend(
                    types.SimpleNamespace(name=":201"), temp, events.append,
                    {"health": object(), "ammo": object()})
                self.assertTrue(backend.owner is instances[0][2])
                self.assertEqual(instances[0][:2],
                                 (":201", Path(temp) / "input-owner-process"))
                self.assertEqual(events, [{
                    "event": "input_owner_process_ready",
                    "schema": "input-owner-process-ready-v1",
                    "owner_id": "owner-7", "service_pid": 45678,
                    "service_start_ticks": 98765,
                    "display": ":201",
                    "receipt_path": str(instances[0][2].receipt_path),
                }])
                self.assertEqual(backend.close(), "closed")
                self.assertEqual(backend.owner.calls, ["close"])
                with self.assertRaisesRegex(RuntimeError, "ready channel failed"):
                    candidate.Backend(
                        types.SimpleNamespace(name=":201"), temp,
                        lambda _event: (_ for _ in ()).throw(
                            RuntimeError("ready channel failed")),
                        {"health": object(), "ammo": object()})
                self.assertEqual(instances[-1][2].calls, ["close"])
        finally:
            if old_base is None:
                sys.modules.pop(base.__name__, None)
            else:
                sys.modules[base.__name__] = old_base
            if old_process is None:
                sys.modules.pop(process_module.__name__, None)
            else:
                sys.modules[process_module.__name__] = old_process


if __name__ == "__main__":
    unittest.main()

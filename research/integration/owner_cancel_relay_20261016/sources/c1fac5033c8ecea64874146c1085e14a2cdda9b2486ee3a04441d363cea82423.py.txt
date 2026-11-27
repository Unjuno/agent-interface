"""Pure-Python regression for owner release RPC failure propagation."""
import importlib.util
import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from executor_v12 import Executor

HERE = Path(__file__).resolve().parent


def load_input_owner_v10_without_x11():
    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace()
    xlib.XK = types.SimpleNamespace()
    xlib.display = types.SimpleNamespace()
    xlib.error = types.SimpleNamespace()
    xlib_ext = types.ModuleType("Xlib.ext")
    xlib_ext.xtest = types.SimpleNamespace()
    with patch.dict(sys.modules, {"Xlib": xlib, "Xlib.ext": xlib_ext}):
        spec = importlib.util.spec_from_file_location(
            "_issue59_input_owner_v10", HERE / "input_owner_v10.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.InputOwner


def load_session_v5_backend_without_gui_dependencies():
    session_v4 = types.ModuleType("session_v4")
    session_v4.Backend = type("Backend", (), {})
    session_v4.suite = types.SimpleNamespace()
    input_owner = types.ModuleType("input_owner")
    input_owner.InputOwner = object
    with patch.dict(sys.modules, {"session_v4": session_v4,
                                  "input_owner": input_owner}):
        spec = importlib.util.spec_from_file_location(
            "_issue59_session_v5", HERE / "session_v5.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.Backend


InputOwnerV10 = load_input_owner_v10_without_x11()
SessionBackend = load_session_v5_backend_without_gui_dependencies()


class FailedOwnerReplyQueue:
    def put(self, request):
        _operation, _lease, _key, done, reply = request
        reply.append((False, RuntimeError("injected owner release RPC failure")))
        done.set()


class OwnerReleaseRpcFailureTests(unittest.TestCase):
    def test_owner_rpc_failure_reaches_terminal_as_unverified(self):
        owner = object.__new__(InputOwnerV10)
        owner.closed = False
        owner.stopped = threading.Event()
        owner.stop_requested = threading.Event()
        owner.error = None
        owner.requests = FailedOwnerReplyQueue()

        backend = object.__new__(SessionBackend)
        backend.owner = owner
        backend.held = set()
        backend.sequence = 1
        backend.validate = lambda _steps: None
        backend.execute = lambda _step, _lease, _identifier, _index: None

        events = []
        terminal_seen = threading.Event()

        def emit(row):
            events.append(row)
            if row.get("event") == "terminal":
                terminal_seen.set()

        executor = Executor(backend, emit)
        try:
            executor.submit(
                "release-rpc-failure",
                [{"op": "observe"}],
                1,
                time.perf_counter_ns() + 1_000_000_000,
            )
            self.assertTrue(terminal_seen.wait(2), "terminal event was not emitted")
        finally:
            executor.close()

        terminal = next(row for row in events if row.get("event") == "terminal")
        self.assertEqual(terminal["status"], "failed")
        self.assertIs(terminal["release"]["verified"], False)
        self.assertIn("injected owner release RPC failure", terminal["release"]["error"])


if __name__ == "__main__":
    unittest.main()

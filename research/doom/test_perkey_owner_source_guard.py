"""Fresh-process source selection checks; never construct a native session."""
from __future__ import annotations

import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch


def repo_relative_posix(path, root):
    return Path(path).resolve().relative_to(root).as_posix()


def probe(route, output):
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    for directory in ("observation_tiles", "observation_gating", "live_control", "doom"):
        sys.path.insert(0, str(root / "research" / directory))
    forbidden = []

    def refuse(*args, **kwargs):
        forbidden.append("native/process/thread construction attempted")
        raise AssertionError(forbidden[-1])

    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
        ButtonRelease=5, Button1Mask=256, AnyPropertyType=0, IsViewable=2)
    xlib.XK = types.SimpleNamespace(string_to_keysym=refuse)
    xlib.error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
        BadDrawable=type("BadDrawable", (Exception,), {}))
    xlib.display = types.ModuleType("Xlib.display")
    xlib.display.Display = refuse
    ext = types.ModuleType("Xlib.ext")
    ext.xtest = types.ModuleType("Xlib.ext.xtest")
    ext.xtest.fake_input = refuse
    vd = types.ModuleType("vizdoom")
    vd.DoomGame = refuse
    vd.GameVariable = types.SimpleNamespace()
    sys.modules.update({"Xlib": xlib, "Xlib.display": xlib.display,
        "Xlib.ext": ext, "Xlib.ext.xtest": ext.xtest, "vizdoom": vd})
    observed = {"route": route, "session_boundary_reached": False,
                "owner_instantiated": False, "session_started": False}

    class BoundaryReached(Exception):
        pass

    def session_boundary():
        state = inspect.currentframe().f_back.f_locals
        backend = state["selected_backend"]
        owner = backend.__init__.__globals__["InputOwner"]
        observed.update({
            "session_boundary_reached": True,
            "backend_module": backend.__module__,
            "owner_file": repo_relative_posix(inspect.getfile(owner), root),
        })
        raise BoundaryReached()

    with patch.object(subprocess, "Popen", refuse), patch.object(threading.Thread, "start", refuse):
        import session_map01_v12 as base
        base.suite.Session = session_boundary
        if route == "v12-cached-perkey":
            import input_owner_v12  # current owner cached before the opt-in selection
        sys.argv = ["session-probe", "--out", str(output), "--seed", "17"]
        if route.endswith("perkey"):
            sys.argv.append("--per-key-input-measurement")
        try:
            if route.startswith("v15"):
                import session_map01_v15
                session_map01_v15.main()
            else:
                base.main()
        except BoundaryReached:
            observed["outcome"] = "selected"
        except RuntimeError as error:
            observed.update(outcome="rejected", error=str(error))
        else:
            raise AssertionError("neither rejection nor session boundary observed")

    observed["forbidden_calls"] = forbidden
    observed["manifest_written"] = (output / "sources.json").exists()
    cached = sys.modules.get("input_owner_v12")
    observed["cached_owner_file"] = repo_relative_posix(cached.__file__, root)
    observed["cached_owner_sha256"] = hashlib.sha256(Path(cached.__file__).read_bytes()).hexdigest()
    observed["expected_owner_file"] = repo_relative_posix(base.PERKEY_OWNER, root)
    observed["expected_owner_sha256"] = hashlib.sha256(base.PERKEY_OWNER.read_bytes()).hexdigest()
    if observed["manifest_written"]:
        manifest = json.loads((output / "sources.json").read_text())
        observed["recorded_a01_owner_sha256"] = manifest.get(str(base.PERKEY_OWNER.relative_to(root / "research")))
    print(json.dumps(observed, sort_keys=True))


class PerKeyOwnerSourceGuardTest(unittest.TestCase):
    def run_route(self, route):
        with tempfile.TemporaryDirectory(prefix="perkey-guard-") as temporary:
            command = [sys.executable, "-B", str(Path(__file__).resolve()), "--probe", route,
                       str(Path(temporary) / "runtime")]
            child = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(child.returncode, 0, child.stderr)
        observed = json.loads(child.stdout)
        print(json.dumps(observed, sort_keys=True), flush=True)
        self.assertEqual(observed["forbidden_calls"], [])
        self.assertIs(observed["owner_instantiated"], False)
        self.assertIs(observed["session_started"], False)
        return observed

    def assert_rejected(self, observed):
        self.assertEqual(observed["outcome"], "rejected")
        self.assertIn("per-key measurement owner source mismatch", observed["error"])
        self.assertIs(observed["session_boundary_reached"], False)
        self.assertIs(observed["manifest_written"], False)
        self.assertEqual(observed["cached_owner_file"], "research/live_control/input_owner_v12.py")

    def test_v12_perkey_keeps_the_requested_owner(self):
        observed = self.run_route("v12-perkey")
        self.assertEqual(observed["outcome"], "selected")
        self.assertEqual(observed["owner_file"], observed["expected_owner_file"])
        self.assertEqual(observed["recorded_a01_owner_sha256"], observed["expected_owner_sha256"])

    def test_v12_cached_owner_rejects_before_session(self):
        self.assert_rejected(self.run_route("v12-cached-perkey"))

    def test_v15_default_keeps_release_batch_owner(self):
        observed = self.run_route("v15-default")
        self.assertEqual(observed["outcome"], "selected")
        self.assertEqual(observed["backend_module"], "doom_owner_thread_release_batch_backend_v1")
        self.assertEqual(observed["owner_file"], "research/live_control/input_transition_owner_v4.py")

    def test_v15_perkey_rejects_before_session(self):
        self.assert_rejected(self.run_route("v15-perkey"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--probe":
        probe(sys.argv[2], Path(sys.argv[3]))
    else:
        unittest.main()

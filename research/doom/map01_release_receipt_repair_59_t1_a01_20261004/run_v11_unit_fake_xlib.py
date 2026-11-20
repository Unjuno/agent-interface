"""Run the checked-out V11 contract tests with the frozen FakeDisplay stubs."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIXTURE_COMMIT = "69b2a53a251f91c4b76955d26bcb7888083cfd08"
FIXTURE_PATH = "research/doom/map01_cancel_keycode_identity_59_t0_a01_20261004/probe.py"
FIXTURE_BLOB = "3b917891c88096b79a46ebcffeb581fa1e174186"


def main():
    fixture_source = subprocess.check_output(
        ["git", "show", f"{FIXTURE_COMMIT}:{FIXTURE_PATH}"], cwd=ROOT)
    actual = hashlib.sha1(b"blob " + str(len(fixture_source)).encode() + b"\0" + fixture_source).hexdigest()
    if actual != FIXTURE_BLOB:
        raise RuntimeError(f"fake-Xlib fixture blob mismatch: {actual}")
    fixture = types.ModuleType("cancel_keycode_fixture")
    sys.modules[fixture.__name__] = fixture
    exec(compile(fixture_source.decode("utf-8"), FIXTURE_PATH, "exec"), fixture.__dict__)
    fixture.load_candidate()

    sys.path.insert(0, str(ROOT / "research/doom"))
    sys.path.insert(0, str(ROOT / "research/live_control"))
    test_path = ROOT / "research/live_control/test_input_owner_v11.py"
    test_spec = importlib.util.spec_from_file_location("test_input_owner_v11", test_path)
    tests = importlib.util.module_from_spec(test_spec)
    sys.modules[test_spec.name] = tests
    test_spec.loader.exec_module(tests)
    class BackendBase:
        def execute(self, *_args, **_kwargs):
            return None

    previous_backend = types.ModuleType("doom_typed_release_backend_v1")
    previous_backend.Backend = BackendBase
    previous_backend.suite = object()
    sys.modules[previous_backend.__name__] = previous_backend
    backend_test_path = ROOT / "research/doom/test_doom_typed_release_backend_v2.py"
    backend_spec = importlib.util.spec_from_file_location(
        "test_doom_typed_release_backend_v2", backend_test_path)
    backend_tests = importlib.util.module_from_spec(backend_spec)
    sys.modules[backend_spec.name] = backend_tests
    backend_spec.loader.exec_module(backend_tests)
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromModule(tests),
        unittest.defaultTestLoader.loadTestsFromModule(backend_tests),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return {
        "schema": "map01-v11-release-contracts-fake-xlib-v1",
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "fixture": {"commit": FIXTURE_COMMIT, "path": FIXTURE_PATH, "blob": FIXTURE_BLOB},
        "tested_sources": {
            "research/live_control/input_owner_v10.py": hashlib.sha256(
                (ROOT / "research/live_control/input_owner_v10.py").read_bytes()).hexdigest(),
            "research/live_control/input_owner_v11.py": hashlib.sha256(
                (ROOT / "research/live_control/input_owner_v11.py").read_bytes()).hexdigest(),
            "research/live_control/test_input_owner_v11.py": hashlib.sha256(
                test_path.read_bytes()).hexdigest(),
            "research/doom/doom_typed_release_backend_v2.py": hashlib.sha256(
                (ROOT / "research/doom/doom_typed_release_backend_v2.py").read_bytes()).hexdigest(),
            "research/doom/test_doom_typed_release_backend_v2.py": hashlib.sha256(
                backend_test_path.read_bytes()).hexdigest(),
        },
    }, result.wasSuccessful()


if __name__ == "__main__":
    record, success = main()
    print(json.dumps(record, indent=2, sort_keys=True))
    raise SystemExit(0 if success else 1)

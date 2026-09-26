"""Construction tests for the v13 pre-guard clock diagnostic wrapper."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PYTHON = sys.executable


class FakeGuard:
    contract = {
        "format": "action-validity-contract-v1",
        "source": {"signals": {"health": {}, "ammo": {}}},
    }

    def __init__(self, *, inverted: bool):
        self.inverted = inverted
        self.called = False

    def receipt(self):
        return {"state": "INPUT_ACTIVE"}

    def check_current(self, snapshot, decided_ns):
        self.called = True
        if self.inverted and decided_ns < snapshot["capture_ns"]:
            raise ValueError("controller decision precedes current snapshot")
        return {"state": "INPUT_ACTIVE"}


def typed_event(capture_ns: int) -> dict:
    return {
        "event": "typed_observation",
        "schema": "doom-typed-observation-v1",
        "id": "construction-test",
        "step": 1,
        "sequence": 7,
        "capture_ns": capture_ns,
        "typed_extraction_started_ns": capture_ns,
        "typed_ready_ns": capture_ns,
        "capture_to_typed_ready_ms": 0.0,
        "artifact_published": False,
        "grants_input_authority": False,
        "frame_rgb_sha256": "a" * 64,
        "frame_size": [2, 2],
        "pointer_binding": {},
        "emit_ns": capture_ns,
        "signals": {
            name: {
                "signal_id": name,
                "sequence": 7,
                "capture_ns": capture_ns,
                "binding": {},
                "status": "unknown",
                "value": None,
            }
            for name in ("health", "ammo")
        },
    }


def load_effective_module(directory: Path):
    effective = directory / "effective.py"
    subprocess.run(
        [PYTHON, "-B", str(HERE / "adapter_v13.py"), "--prepare-only", str(effective)],
        cwd=REPO,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
    )
    sys.path[:0] = [str(REPO / "research/doom"), str(REPO / "research/live_control")]
    spec = importlib.util.spec_from_file_location("v13_diagnostic_test_controller", effective)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class DiagnosticCaptureTests(unittest.TestCase):
    def test_inverted_operands_are_durable_before_original_guard_exception(self):
        with tempfile.TemporaryDirectory(prefix="v13-clock-test-") as temp:
            root = Path(temp)
            module = load_effective_module(root)
            guard = FakeGuard(inverted=True)
            monitor = module.DoomRunningActionMonitor(guard, None, None)
            monitor.clock_boundary_log = root / "boundary.jsonl"
            module._RUNTIME_CLOCK_OFFSET_LOWER = 0
            module._RUNNING_ACTION_CLOCK_CALIBRATION = {
                "stage": "test", "same_session": True,
                "host_domain": "host_monotonic_ns",
                "runtime_domain": "runtime_monotonic_ns",
                "samples": [{"host_send_ns": 90, "runtime_ns": 100,
                             "host_receive_ns": 95, "offset_lower_ns": 5,
                             "offset_upper_ns": 10}],
            }
            module.time.perf_counter_ns = lambda: 100
            with self.assertRaisesRegex(ValueError, "controller decision precedes current snapshot"):
                monitor.observe(typed_event(101))
            row = json.loads(monitor.clock_boundary_log.read_text(encoding="utf-8"))
            self.assertEqual(row["sequence"], 7)
            self.assertEqual(row["capture_ns"], 101)
            self.assertEqual(row["controller_decided_ns"], 100)
            self.assertEqual(row["comparison_delta_ns"], -1)
            self.assertEqual(row["calibration"]["stage"], "test")
            self.assertEqual(len(row["calibration"]["samples"]), 1)
            self.assertEqual(len(row["calibration_sha256"]), 64)
            self.assertTrue(guard.called)

    def test_log_failure_stops_before_guard(self):
        with tempfile.TemporaryDirectory(prefix="v13-clock-test-") as temp:
            root = Path(temp)
            module = load_effective_module(root)
            guard = FakeGuard(inverted=False)
            monitor = module.DoomRunningActionMonitor(guard, None, None)
            monitor.clock_boundary_log = root / "missing" / "boundary.jsonl"
            module._RUNTIME_CLOCK_OFFSET_LOWER = 100
            module.time.perf_counter_ns = lambda: 200
            with self.assertRaises(OSError):
                monitor.observe(typed_event(100))
            self.assertFalse(guard.called)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "audit_passive_process_activity", HERE / "audit_passive_process_activity.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def fixture_rows():
    rows = []
    for n in range(3):
        rows.append({
            "repetition": n, "setup": "initialized", "mode_readback": "Mode.ASYNC_SPECTATOR",
            "ticrate_readback": 35,
            "wad_sha256": "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b",
            "advancing_api_calls": 0, "closed": True, "scorer_status": "returned",
            "samples": [{"tic": 1} for _ in range(20)], "process_clk_tck": 100,
            "elapsed_ns": 1_500_000_000, "initial_tic": 1, "final_tic": 1,
            "child_cpu_deltas": [{"comm": "vizdoom", "end_state": "S", "cpu_ticks_delta": 2}],
            "clock_progress_observed": False, "scorer_call_span_ns": 30000,
        })
    return rows


class PassiveProcessActivityAuditTest(unittest.TestCase):
    def test_three_static_passive_sessions_hold(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            raw.write_text(json.dumps(fixture_rows()))
            report = AUDIT.audit(raw)
            self.assertEqual(report["decision"], "HOLD_API_TIC_STATIC_PROCESS_ACTIVITY_UNRESOLVED")
            self.assertEqual(report["errors"], [])
            self.assertFalse(report["formal_allocation"])

    def test_incomplete_session_fails_audit(self):
        rows = fixture_rows()[:2]
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            raw.write_text(json.dumps(rows))
            report = AUDIT.audit(raw)
            self.assertEqual(report["decision"], "FAIL_AUDIT")
            self.assertTrue(report["errors"])

    def test_changed_tic_fails_audit(self):
        rows = fixture_rows()
        rows[0]["samples"][0]["tic"] = 2
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            raw.write_text(json.dumps(rows))
            report = AUDIT.audit(raw)
            self.assertEqual(report["decision"], "FAIL_AUDIT")
            self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()

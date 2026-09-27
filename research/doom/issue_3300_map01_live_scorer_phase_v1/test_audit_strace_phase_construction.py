import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "audit_strace_phase_construction", HERE / "audit_strace_phase_construction.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def fixture_rows():
    rows = []
    for rep in range(3):
        mono = 10_000_000_000 + rep * 2_000_000_000
        wall = 1_789_911_000_000_000_000 + rep * 2_000_000_000
        anchor = {"wall_before_ns": wall - 20, "monotonic_ns": mono,
                  "wall_after_ns": wall + 20}
        scorer_anchor = {"wall_before_ns": wall + 1_500_000_000 - 20,
                         "monotonic_ns": mono + 1_500_000_000,
                         "wall_after_ns": wall + 1_500_000_000 + 20}
        end_anchor = {"wall_before_ns": wall + 1_700_000_000 - 20,
                      "monotonic_ns": mono + 1_700_000_000,
                      "wall_after_ns": wall + 1_700_000_000 + 20}
        rows.append({
            "repetition": rep, "setup": "initialized",
            "mode": "Mode.ASYNC_SPECTATOR", "ticrate": 35,
            "wad_sha256": "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b",
            "scorer_status": "returned", "closed": True,
            "advancing_api_calls": 0, "initial_api_tic": 1, "final_api_tic": 1,
            "elapsed_ns": 1_500_000_000,
            "anchors": [anchor],
            "scorer_call_start_anchor": scorer_anchor,
            "scorer_call_end_anchor": scorer_anchor,
            "post_scorer_end": end_anchor,
            "scorer_api_trace": [{"name": "get_episode_time", "start_ns": mono + 750_000_000}],
        })
    return rows


def trace_text(missing=False):
    lines = []
    for rep in range(3):
        wall = 1_789_911_000_000_000_000 + rep * 2_000_000_000
        for tic in range(6, 60):
            if missing and rep == 1 and tic == 20:
                continue
            timestamp = wall + (tic - 6) * 28_571_429
            seconds = f"{timestamp // 1_000_000_000}.{timestamp % 1_000_000_000:09d}"
            lines.append(
                f'10 {seconds} write(1, "VIZ_Tic: tic: {tic}, vizTime: {tic}\\n", 28) = 28 <0.000010>'
            )
    return "\n".join(lines) + "\n"


class StracePhaseAuditTest(unittest.TestCase):
    def test_same_clock_contiguous_tic_records_are_construction_only(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            trace = Path(td) / "strace.txt"
            raw.write_text(json.dumps(fixture_rows()))
            trace.write_text(trace_text())
            report = AUDIT.audit(raw, trace)
            self.assertEqual(report["decision"], "PASS_CONSTRUCTION_ONLY_SAME_CLOCK_TIC_LOG_CORRELATION")
            self.assertEqual(report["errors"], [])
            self.assertFalse(report["formal_allocation"])
            position = report["rows"][0]["scorer_getter_positions_vs_logged_tics"][0]
            self.assertIsNotNone(position["preceding_log_to_getter_start_ns_interval"])
            self.assertIsNotNone(position["getter_start_to_next_log_ns_interval"])

    def test_missing_tic_record_breaks_contiguous_gate(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            trace = Path(td) / "strace.txt"
            raw.write_text(json.dumps(fixture_rows()))
            trace.write_text(trace_text(missing=True))
            report = AUDIT.audit(raw, trace)
            self.assertEqual(report["decision"], "FAIL_AUDIT")
            self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()

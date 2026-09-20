import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "audit_engine_tic_debug_construction", HERE / "audit_engine_tic_debug_construction.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def rows():
    result = []
    for repetition in range(3):
        result.append({
            "repetition": repetition, "setup": "initialized",
            "mode_readback": "Mode.ASYNC_SPECTATOR", "ticrate_readback": 35,
            "advancing_api_calls": 0, "closed": True, "scorer_status": "returned",
            "initial_api_tic": 1, "final_api_tic": 1,
            "elapsed_ns": 1_500_000_000,
            "samples": [{"api_tic": 1} for _ in range(20)],
        })
    return result


def log_text():
    output = []
    for repetition in range(3):
        output.append(f"RUN31_PASSIVE_BEGIN repetition={repetition}")
        for tic in range(6, 59):
            output.append(f"VIZ_Tic: tic: {tic}, vizTime: {tic}")
        output.append(f"RUN31_PASSIVE_END repetition={repetition}")
    return "\n".join(output) + "\n"


class EngineTicDebugAuditTest(unittest.TestCase):
    def test_internal_tics_progress_while_api_snapshot_stays_fixed(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            log = Path(td) / "container.log"
            raw.write_text(json.dumps(rows()))
            log.write_text(log_text())
            report = AUDIT.audit(raw, log)
            self.assertEqual(report["decision"], "PASS_CONSTRUCTION_ONLY_INTERNAL_TIC_PROGRESS_API_SNAPSHOT_STALE")
            self.assertEqual(report["errors"], [])
            self.assertFalse(report["formal_allocation"])

    def test_substantial_missing_tic_trace_fails(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            log = Path(td) / "container.log"
            raw.write_text(json.dumps(rows()))
            original = log_text().splitlines()
            removed = 0
            damaged = []
            for line in original:
                if line.startswith("VIZ_Tic:") and removed < 20:
                    removed += 1
                    continue
                damaged.append(line)
            log.write_text("\n".join(damaged) + "\n")
            report = AUDIT.audit(raw, log)
            self.assertEqual(report["decision"], "FAIL_AUDIT")
            self.assertTrue(report["errors"])

    def test_advancement_call_is_rejected(self):
        data = rows()
        data[1]["advancing_api_calls"] = 1
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            log = Path(td) / "container.log"
            raw.write_text(json.dumps(data))
            log.write_text(log_text())
            report = AUDIT.audit(raw, log)
            self.assertEqual(report["decision"], "FAIL_AUDIT")
            self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()

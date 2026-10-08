import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_shm_visibility", HERE / "audit_shm_visibility.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def fixture():
    start = 10_000_000_000
    return {
        "setup": "initialized", "shm_open_fd": 4, "shm_errno": 0,
        "shm_size": 2_634_640,
        "samples": [
            {"mono_before_ns": start + i * 3_000_000,
             "mono_after_ns": start + i * 3_000_000 + 1000,
             "game_tic": 4, "map_tic": 1, "api_tic": 1}
            for i in range(481)
        ],
    }


class ShmVisibilityAuditTest(unittest.TestCase):
    def test_static_shared_snapshot_is_scoped_construction_pass(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "raw.json"
            path.write_text(json.dumps(fixture()))
            report = AUDIT.audit(path)
            self.assertEqual(report["decision"], "PASS_CONSTRUCTION_ONLY_SHM_SNAPSHOT_STALE")
            self.assertEqual(report["errors"], [])
            self.assertFalse(report["formal_allocation"])

    def test_changed_snapshot_value_fails_the_fixed_result_gate(self):
        data = fixture()
        data["samples"][100]["game_tic"] = 5
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "raw.json"
            path.write_text(json.dumps(data))
            self.assertEqual(AUDIT.audit(path)["decision"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main()

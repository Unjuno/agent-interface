import copy
import json
from pathlib import Path
import unittest

from audit import audit

FREEZE = json.loads(Path(__file__).with_name("FREEZE.json").read_text(encoding="utf-8"))
SCHEDULE = FREEZE["expected_schedule"]


def fixture():
    workload = FREEZE["workload"]
    runs = []
    for index, arm in enumerate(SCHEDULE):
        is_wslc = arm == "wslc"
        runs.append({
            "index": index,
            "arm": arm,
            "runtime_identity": FREEZE["wslc_image"] if is_wslc else FREEZE["native_runtime_identity"],
            "python_version": FREEZE["expected_python_version"],
            "source_sha256": copy.deepcopy(workload["source_sha256"]),
            "exit_code": 0,
            "wall_ns": 1_000_000_000 if is_wslc else 800_000_000,
            "max_tree_rss_kib": 120_000 if is_wslc else 100_000,
            "host_psi_total_before": {"some": 100, "full": 20},
            "host_psi_total_after": {"some": 100, "full": 20},
            "tests": [{"id": name, "status": "passed"} for name in workload["expected_test_ids"]],
        })
    return copy.deepcopy(FREEZE), {"schema": "native-wsl2-migration-6389-raw-v1", "runs": runs}


class AuditRepairTests(unittest.TestCase):
    def test_nested_frozen_contract_reaches_scoped_pass_on_synthetic_rows(self):
        freeze, raw = fixture()
        self.assertEqual(audit(raw, freeze)["status"], "PASS_NATIVE_MIGRATION_SCOPED")

    def test_boolean_run_index_is_not_an_integer(self):
        freeze, raw = fixture()
        raw["runs"][0]["index"] = False
        self.assertEqual(audit(raw, freeze)["status"], "HOLD_SCHEDULE_INVALID")

    def test_boolean_exit_code_cannot_encode_success(self):
        freeze, raw = fixture()
        raw["runs"][0]["exit_code"] = False
        self.assertEqual(audit(raw, freeze)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_boolean_wall_time_is_rejected(self):
        freeze, raw = fixture()
        raw["runs"][0]["wall_ns"] = True
        self.assertEqual(audit(raw, freeze)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_boolean_tree_rss_is_rejected(self):
        freeze, raw = fixture()
        raw["runs"][0]["max_tree_rss_kib"] = True
        self.assertEqual(audit(raw, freeze)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_boolean_psi_counter_is_rejected(self):
        freeze, raw = fixture()
        raw["runs"][0]["host_psi_total_before"]["some"] = True
        self.assertEqual(audit(raw, freeze)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_boolean_values_never_produce_pass(self):
        for field in ("index", "exit_code", "wall_ns", "max_tree_rss_kib"):
            freeze, raw = fixture()
            raw["runs"][0][field] = True
            self.assertNotEqual(audit(raw, freeze)["status"], "PASS_NATIVE_MIGRATION_SCOPED")


if __name__ == "__main__":
    unittest.main(verbosity=2)


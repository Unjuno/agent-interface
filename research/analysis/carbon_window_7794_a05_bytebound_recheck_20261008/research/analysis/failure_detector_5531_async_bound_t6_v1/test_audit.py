import copy
import json
import unittest
from pathlib import Path

from audit import audit_records
from candidate import build_records


HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))


class AsyncBoundaryAuditTests(unittest.TestCase):
    def setUp(self):
        self.records = build_records(FREEZE)

    def test_pristine_deadline_matrix_passes(self):
        result = audit_records(self.records, FREEZE)
        self.assertEqual(result["status"], "PASS_ASYNC_DELAY_BOUNDARY_SCOPED", result["errors"])
        self.assertEqual(result["metrics"], {
            "trials": 18,
            "raw_rows": 114,
            "prefix_groups": 6,
            "healthy_terminal_failures_at_deadline": 3,
            "effectful_actions": 0,
        })

    def test_divergent_no_heartbeat_prefix_is_rejected(self):
        rows = copy.deepcopy(self.records)
        target = next(row for row in rows if row["world"] == "crashed"
                      and row["policy"] == "typed_suspicion" and row["deadline"] == 3
                      and row["event"] == "NO_HEARTBEAT" and row["tick"] == 2)
        target["observation"]["heartbeat_sequence"] = 1
        self.assertTrue(audit_records(rows, FREEZE)["errors"])

    def test_suspicion_cannot_enable_routing(self):
        rows = copy.deepcopy(self.records)
        target = next(row for row in rows if row["world"] == "healthy_slow"
                      and row["policy"] == "typed_suspicion" and row["deadline"] == 3
                      and row["event"] == "TIMEOUT_DECISION")
        target["route_enabled"] = True
        self.assertTrue(audit_records(rows, FREEZE)["errors"])

    def test_late_old_generation_response_cannot_reactivate_failure(self):
        rows = copy.deepcopy(self.records)
        target = next(row for row in rows if row["world"] == "crashed"
                      and row["policy"] == "typed_suspicion" and row["deadline"] == 3
                      and row["event"] == "LATE_OLD_GENERATION_RESPONSE")
        target.update(state="AVAILABLE", route_enabled=True, authority_revoked=False,
                      authority_generation=1)
        self.assertTrue(audit_records(rows, FREEZE)["errors"])

    def test_invalid_response_cannot_clear_suspicion(self):
        rows = copy.deepcopy(self.records)
        target = next(row for row in rows if row["world"] == "invalid_response"
                      and row["policy"] == "typed_suspicion" and row["deadline"] == 3
                      and row["event"] == "INVALID_UNAUTHENTICATED_RESPONSE")
        target.update(state="AVAILABLE", route_enabled=True)
        self.assertTrue(audit_records(rows, FREEZE)["errors"])


if __name__ == "__main__":
    unittest.main()

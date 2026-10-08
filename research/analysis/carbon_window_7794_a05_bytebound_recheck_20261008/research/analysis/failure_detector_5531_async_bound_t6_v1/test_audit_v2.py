import copy
import json
import unittest
from pathlib import Path

from audit_v2 import audit_records
from candidate import build_records


HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
AUDIT_FREEZE = json.loads((HERE / "AUDIT_V2_FREEZE.json").read_text(encoding="utf-8"))


class CorrectiveAuditV2Tests(unittest.TestCase):
    def setUp(self):
        self.records = build_records(FREEZE)

    def run_mutation(self, predicate, mutate):
        records = copy.deepcopy(self.records)
        mutate(next(row for row in records if predicate(row)))
        result = audit_records(records, AUDIT_FREEZE)
        self.assertTrue(result["errors"])
        self.assertEqual(result["status"], "FAIL_AUDIT_V2")

    def test_pristine_trace_passes_corrective_audit(self):
        result = audit_records(self.records, AUDIT_FREEZE)
        self.assertEqual(result["status"], "PASS_ASYNC_DELAY_BOUNDARY_SCOPED_AUDIT_V2", result["errors"])
        self.assertEqual(result["metrics"]["authenticated_proof_rows_checked"], 24)
        self.assertEqual(result["metrics"]["effectful_actions"], 0)

    def test_missing_fresh_heartbeat_authentication_is_rejected(self):
        self.run_mutation(lambda r: r["world"] == "healthy_slow" and r["policy"] == "typed_suspicion"
                          and r["deadline"] == 3 and r["event"] == "FRESH_AUTHENTICATED_HEARTBEAT",
                          lambda r: r.update(authenticated=False))

    def test_wrong_fresh_heartbeat_generation_is_rejected(self):
        self.run_mutation(lambda r: r["world"] == "healthy_slow" and r["policy"] == "typed_suspicion"
                          and r["deadline"] == 3 and r["event"] == "FRESH_AUTHENTICATED_HEARTBEAT",
                          lambda r: r.update(response_generation=0))

    def test_missing_crash_witness_authentication_is_rejected(self):
        self.run_mutation(lambda r: r["world"] == "crashed" and r["policy"] == "typed_suspicion"
                          and r["deadline"] == 3 and r["event"] == "INDEPENDENT_CRASH_WITNESS",
                          lambda r: r.update(authenticated=False))

    def test_wrong_crash_witness_domain_is_rejected(self):
        self.run_mutation(lambda r: r["world"] == "crashed" and r["policy"] == "typed_suspicion"
                          and r["deadline"] == 3 and r["event"] == "INDEPENDENT_CRASH_WITNESS",
                          lambda r: r.update(witness_domain="subject-channel"))

    def test_suspicion_cannot_enable_routing(self):
        self.run_mutation(lambda r: r["world"] == "healthy_slow" and r["policy"] == "typed_suspicion"
                          and r["deadline"] == 3 and r["event"] == "TIMEOUT_DECISION",
                          lambda r: r.update(route_enabled=True))

    def test_late_old_generation_response_cannot_reactivate_terminal_failure(self):
        self.run_mutation(lambda r: r["world"] == "crashed" and r["policy"] == "typed_suspicion"
                          and r["deadline"] == 3 and r["event"] == "LATE_OLD_GENERATION_RESPONSE",
                          lambda r: r.update(state="AVAILABLE", route_enabled=True,
                                             authority_revoked=False, authority_generation=1))

    def test_invalid_response_cannot_clear_suspicion(self):
        self.run_mutation(lambda r: r["world"] == "invalid_response" and r["policy"] == "typed_suspicion"
                          and r["deadline"] == 3 and r["event"] == "INVALID_UNAUTHENTICATED_RESPONSE",
                          lambda r: r.update(state="AVAILABLE", route_enabled=True))

    def test_missing_required_event_is_rejected(self):
        records = copy.deepcopy(self.records)
        records.remove(next(r for r in records if r["world"] == "crashed" and r["policy"] == "typed_suspicion"
                            and r["deadline"] == 3 and r["event"] == "INDEPENDENT_CRASH_WITNESS"))
        result = audit_records(records, AUDIT_FREEZE)
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()

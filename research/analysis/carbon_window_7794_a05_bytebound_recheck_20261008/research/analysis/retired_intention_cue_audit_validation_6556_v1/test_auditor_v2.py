import copy
import json
import sys
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "retired_intention_cue_6556_t0_v1"
sys.path.insert(0, str(PACKAGE))

import auditor_v2  # noqa: E402

FIXTURE = json.loads((PACKAGE / "fixture.json").read_text(encoding="utf-8"))
ORACLE = json.loads((PACKAGE / "oracle.json").read_text(encoding="utf-8"))
RAW = json.loads((PACKAGE / "formal_01_20261002" / "candidate_output" / "candidate.raw.json").read_text(encoding="utf-8"))
FENCE = "ORIGIN_GENERATION_RETIREMENT_FENCE"


def mutate(case_id, policy, **changes):
    raw = copy.deepcopy(RAW)
    row = next(row for row in raw["rows"] if row["case_id"] == case_id and row["policy"] == policy)
    row.update(changes)
    return raw


class AuditValidationTests(unittest.TestCase):
    def test_immutable_formal_raw_still_passes(self):
        result = auditor_v2.audit(FIXTURE, ORACLE, RAW)
        self.assertEqual(result["status"], "METHOD_PASS_SCOPED")
        self.assertEqual(result["rows_seen"], 50)
        self.assertEqual(result["errors"], [])

    def test_arbitrary_decision_token_is_rejected(self):
        result = auditor_v2.audit(FIXTURE, ORACLE, mutate("old_event_original_instance", FENCE, decision="GARBAGE"))
        self.assertEqual(result["status"], "FAIL_OR_HOLD")
        self.assertTrue(any(error["kind"] == "invalid_decision" for error in result["errors"]))

    def test_known_retired_lineage_cannot_be_unknown(self):
        result = auditor_v2.audit(FIXTURE, ORACLE, mutate("old_event_original_instance", FENCE, decision="UNKNOWN"))
        self.assertEqual(result["status"], "FAIL_OR_HOLD")
        self.assertTrue(any(error["kind"] == "origin_fence_decision_mismatch" for error in result["errors"]))

    def test_eligible_fresh_lineage_cannot_be_refused(self):
        result = auditor_v2.audit(FIXTURE, ORACLE, mutate("fresh_reused_cue_generation_B", FENCE, decision="REFUSE"))
        self.assertEqual(result["status"], "FAIL_OR_HOLD")
        self.assertTrue(any(error["kind"] == "origin_fence_decision_mismatch" for error in result["errors"]))

    def test_missing_origin_must_remain_unknown(self):
        result = auditor_v2.audit(FIXTURE, ORACLE, mutate("old_event_rebound_missing_origin", FENCE, decision="REFUSE"))
        self.assertEqual(result["status"], "FAIL_OR_HOLD")
        self.assertTrue(any(error["kind"] == "origin_fence_decision_mismatch" for error in result["errors"]))

    def test_comparator_does_not_emit_unknown(self):
        result = auditor_v2.audit(FIXTURE, ORACLE, mutate("old_event_original_instance", "DURABLE_INSTANCE_EVENT_ID", decision="UNKNOWN"))
        self.assertEqual(result["status"], "FAIL_OR_HOLD")
        self.assertTrue(any(error["kind"] == "unexpected_unknown_for_comparator" for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()

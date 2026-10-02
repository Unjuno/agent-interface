"""Construction tests for the strict T2 raw auditor; no formal candidate run."""
import json
import unittest
from pathlib import Path

from run_candidate import build_packets
from strict_auditor import audit_packet

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "T2_SPEC.json").read_text(encoding="utf-8"))
RAW = json.loads((ROOT / "input/raw_packets.json").read_text(encoding="utf-8"))


class StrictAuditorT2Tests(unittest.TestCase):
    def setUp(self):
        self.packets = build_packets(RAW)

    def test_contract_complete_control_is_accepted(self):
        self.assertEqual(self.packets[0]["case_id"], "CONTROL_CONTRACT_COMPLETE")
        self.assertEqual(audit_packet(self.packets[0]["packet"], SPEC["expected_external_binding"]), [])

    def test_common_mode_binding_rebind_is_rejected(self):
        errors = audit_packet(self.packets[1]["packet"], SPEC["expected_external_binding"])
        self.assertTrue(any("external_binding_mismatch" in row for row in errors))

    def test_each_authority_or_decision_contradiction_is_rejected(self):
        for row in self.packets[2:5]:
            with self.subTest(case=row["case_id"]):
                self.assertTrue(audit_packet(row["packet"], SPEC["expected_external_binding"]))

    def test_missing_required_guard_fields_is_rejected(self):
        errors = audit_packet(self.packets[5]["packet"], SPEC["expected_external_binding"])
        self.assertTrue(any("may_only_preserve_or_reduce_existing_authority_type" in x or
                            "may_only_preserve_or_reduce_existing_authority_value" in x or
                            "semantic_change_identified_type" in x or
                            "semantic_change_identified_value" in x for x in errors))

    def test_boolean_false_is_not_interchangeable_with_integer_zero(self):
        packet = json.loads(json.dumps(self.packets[0]["packet"]))
        case = next(row for row in packet["cases"] if row["case_id"] == "ONE_SOFT")
        case["raw_events"][-1]["outcome"]["grants_input_authority"] = 0
        self.assertTrue(audit_packet(packet, SPEC["expected_external_binding"]))

    def test_t1_control_payload_remains_unchanged_and_incomplete(self):
        raw_control = RAW["runs"][0]["packet"]
        one = next(row for row in raw_control["cases"] if row["case_id"] == "ONE_SOFT")
        outcome = one["raw_events"][-1]["outcome"]
        self.assertNotIn("may_only_preserve_or_reduce_existing_authority", outcome)
        self.assertNotIn("semantic_change_identified", outcome)


if __name__ == "__main__":
    unittest.main()


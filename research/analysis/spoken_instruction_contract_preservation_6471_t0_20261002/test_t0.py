import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("issue6471_candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(candidate)
AUDIT_SPEC = importlib.util.spec_from_file_location("issue6471_audit", ROOT / "audit.py")
audit = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(audit)
CASES = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
BY_ID = {case["id"]: case for case in CASES}


class T0ConstructionTests(unittest.TestCase):
    def test_all_frozen_cases_have_decisions_and_no_integrity_errors(self):
        rows = [candidate.evaluate(case) for case in CASES]
        self.assertEqual(len(rows), 7)
        self.assertEqual({row["case_id"] for row in rows}, set(BY_ID))
        self.assertTrue(all(row["decision"] != "STOP_INTEGRITY" and not row["errors"] for row in rows))

    def test_equal_wer_pair_separates_filler_noise_from_recipient_change(self):
        source = BY_ID["benign_filler_drop"]["source_text"].lower().split()
        benign = BY_ID["benign_filler_drop"]["transcript"].lower().split()
        swapped = BY_ID["recipient_swap_equal_wer"]["transcript"].lower().split()
        self.assertEqual(candidate.evaluate(BY_ID["benign_filler_drop"])["decision"], "ALLOW_TO_SEPARATE_AUTHORITY_GATE")
        self.assertEqual(candidate.evaluate(BY_ID["recipient_swap_equal_wer"])["decision"], "BLOCK")
        self.assertEqual(len(source) - len(benign), 1)
        self.assertEqual(sum(a != b for a, b in zip(source, swapped)), 1)

    def test_negation_homophone_bound_and_force_corruption_block(self):
        for case_id in ("deleted_negation", "homophone_target", "numeric_bound_change", "quoted_explanation_promoted_to_action"):
            with self.subTest(case_id=case_id):
                self.assertEqual(candidate.evaluate(BY_ID[case_id])["decision"], "BLOCK")

    def test_genuine_ambiguity_only_clarifies(self):
        self.assertEqual(candidate.evaluate(BY_ID["genuine_recipient_ambiguity"])["decision"], "CLARIFY")

    def test_bad_source_offset_fails_closed(self):
        case = json.loads(json.dumps(BY_ID["benign_filler_drop"]))
        case["span_links"]["recipient"]["source"] = "Not in source"
        row = candidate.evaluate(case)
        self.assertEqual(row["decision"], "STOP_INTEGRITY")
        self.assertIn("SOURCE_SPAN_MISSING:recipient", row["errors"])

    def test_candidate_never_returns_execution_authority(self):
        self.assertTrue(all(candidate.evaluate(case)["decision"] != "EXECUTE" for case in CASES))

    def test_independent_oracle_rejects_slot_and_span_label_mutations(self):
        for case in CASES:
            self.assertEqual(audit.audit_case(case, candidate.evaluate(case)), [], case["id"])
        mutations = (
            ("recipient_swap_equal_wer", "transcript_slots", "recipient", "Alice"),
            ("deleted_negation", "source_contract", "forbidden", []),
            ("quoted_explanation_promoted_to_action", "source_contract", "speech_act", "EXECUTE_REQUEST"),
            ("homophone_target", "span_links", "recipient", {"source": "May", "transcript": "May"}),
        )
        for case_id, field, key, value in mutations:
            with self.subTest(case_id=case_id, field=field):
                case = json.loads(json.dumps(BY_ID[case_id]))
                case[field][key] = value
                self.assertTrue(audit.audit_case(case, candidate.evaluate(BY_ID[case_id])))


if __name__ == "__main__":
    unittest.main()

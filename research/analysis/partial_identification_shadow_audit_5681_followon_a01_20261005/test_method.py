import copy
import json
import unittest

from audit import audit_document
from candidate import analyze


def frame(case_id, labels, threshold="1/2", *, complete=True, out_of_frame=False):
    return {
        "case_id": case_id,
        "capture_frame_complete": complete,
        "out_of_frame_transition_known": out_of_frame,
        "threshold": threshold,
        "rows": [
            {
                "capture_id": f"{case_id}-{index}",
                "label": label,
                "audit_inclusion_probability": "0/1" if label == "unknown" else "1/1",
            }
            for index, label in enumerate(labels)
        ],
    }


CASES = [
    frame("zero_support_spans", ["positive", "negative", "unknown", "unknown"]),
    frame("all_unknown", ["unknown"] * 4),
    frame("lower_bound_reject", ["positive"] * 3 + ["unknown"]),
    frame("upper_bound_only", ["negative"] * 4 + ["unknown"]),
    frame("upper_touches_threshold", ["positive", "negative", "negative", "unknown"]),
    frame("lower_touches_threshold", ["positive", "positive", "negative", "unknown"]),
    frame("incomplete_denominator", ["negative", "unknown"], complete=False),
    frame("out_of_frame", ["positive", "negative", "unknown"], out_of_frame=True),
]


class PartialIdentificationTests(unittest.TestCase):
    def test_frozen_case_file_matches_literal_test_population(self):
        with open("cases.json", encoding="utf-8") as source:
            self.assertEqual(json.load(source), CASES)

    def test_unknown_labels_produce_bounds_not_a_point_estimate(self):
        result = analyze(CASES[0])
        self.assertEqual(result.get("bounds"), {"lower": "1/4", "upper": "3/4"})
        self.assertNotIn("point_estimate", result)
        self.assertEqual(result.get("frame_decision"), "HOLD_SPANS_THRESHOLD")
        self.assertEqual(result.get("zero_support_unknown_ids"), ["zero_support_spans-2", "zero_support_spans-3"])

    def test_all_unknown_labels_span_the_binary_prevalence_range(self):
        result = analyze(CASES[1])
        self.assertEqual(result.get("bounds"), {"lower": "0/1", "upper": "1/1"})

    def test_whole_interval_below_threshold_is_only_a_method_classification(self):
        result = analyze(CASES[3])
        self.assertEqual(result.get("frame_decision"), "ROBUST_BELOW_THRESHOLD")
        self.assertEqual(result.get("action_authority"), "NONE")
        self.assertEqual(result.get("effect_safety_gate"), "NOT_EVALUATED")

    def test_equality_at_either_interval_endpoint_stays_on_hold(self):
        self.assertEqual(analyze(CASES[4]).get("frame_decision"), "HOLD_TOUCHES_THRESHOLD")
        self.assertEqual(analyze(CASES[5]).get("frame_decision"), "HOLD_TOUCHES_THRESHOLD")

    def test_incomplete_capture_denominator_has_no_numeric_bounds(self):
        result = analyze(CASES[6])
        self.assertIsNone(result.get("bounds"))
        self.assertEqual(result.get("frame_decision"), "HOLD_INCOMPLETE_FRAME")

    def test_out_of_frame_transition_does_not_enter_the_captured_frame_bounds(self):
        result = analyze(CASES[7])
        self.assertEqual(result.get("bounds"), {"lower": "1/3", "upper": "2/3"})
        self.assertEqual(result.get("overall_scope"), "HOLD_OUT_OF_FRAME_NOT_IDENTIFIABLE")

    def test_independent_auditor_enumerates_all_unknown_label_completions(self):
        document = {"schema": "partial-identification-candidate-v1", "cases": [analyze(c) for c in CASES]}
        audit = audit_document(CASES, document)
        self.assertEqual(audit["errors"], [])
        self.assertEqual(audit["completion_count"], 4 + 16 + 2 + 2 + 2 + 2 + 2)
        self.assertEqual(audit["mutation_controls_rejected"], 10)

    def test_independent_auditor_rejects_false_narrow_bound_and_promotion(self):
        document = {"schema": "partial-identification-candidate-v1", "cases": [analyze(c) for c in CASES]}
        self.assertEqual(audit_document(CASES, document)["errors"], [])
        for case_id, mutation in (
            ("zero_support_spans", lambda row: row.update(bounds={"lower": "1/2", "upper": "1/2"})),
            ("all_unknown", lambda row: row.update(frame_decision="ROBUST_BELOW_THRESHOLD")),
            ("out_of_frame", lambda row: row.update(overall_scope="METHOD_SCOPE_ONLY")),
            ("incomplete_denominator", lambda row: row.update(bounds={"lower": "0/1", "upper": "1/1"})),
        ):
            corrupt = copy.deepcopy(document)
            row = next(r for r in corrupt["cases"] if r["case_id"] == case_id)
            mutation(row)
            self.assertTrue(audit_document(CASES, corrupt)["errors"], case_id)

    def test_raw_audit_rejects_missing_and_duplicate_cases(self):
        document = {"schema": "partial-identification-candidate-v1", "cases": [analyze(c) for c in CASES]}
        self.assertEqual(audit_document(CASES, document)["errors"], [])
        self.assertTrue(audit_document(CASES, {**document, "cases": document["cases"][:-1]})["errors"])
        duplicate = copy.deepcopy(document)
        duplicate["cases"][-1]["case_id"] = duplicate["cases"][0]["case_id"]
        self.assertTrue(audit_document(CASES, duplicate)["errors"])

    def test_candidate_rejects_duplicate_capture_identity(self):
        duplicate = copy.deepcopy(CASES[0])
        duplicate["rows"][1]["capture_id"] = duplicate["rows"][0]["capture_id"]
        with self.assertRaises(ValueError):
            analyze(duplicate)

    def test_candidate_rejects_boolean_or_malformed_threshold(self):
        malformed = copy.deepcopy(CASES[0])
        malformed["threshold"] = "True"
        with self.assertRaises(ValueError):
            analyze(malformed)


if __name__ == "__main__":
    unittest.main()

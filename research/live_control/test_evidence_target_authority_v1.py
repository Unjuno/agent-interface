"""Direct contract tests that do not depend on the missing Mindustry report."""
import copy
import unittest

from research.live_control.evidence_target_contract_v2 import validate


READINESS = {"status": "READY", "receipts": [
    {"point": [24, 38], "evidence_digest": "receipt-1"}]}


def decision(op, reason, *, receipt_index=0, points=None,
             point_space="not_applicable", motion="not_applicable"):
    return {"op": op, "receipt_index": receipt_index,
            "point_space": point_space, "points": [] if points is None else points,
            "motion_model": motion,
            "evidence_kind": "persistent_hover_tooltip",
            "diagnostic_reason": reason}


class EvidenceTargetAuthorityTests(unittest.TestCase):
    def test_positive_receipt_returns_reference_without_input_authority(self):
        result = validate(decision("target_reference", "matched", receipt_index=1,
            points=[{"x": 24, "y": 38}],
            point_space="source_observation_pixels",
            motion="surface_origin_translation"), READINESS)
        self.assertEqual(result["authority_class"], "TARGET_REFERENCE_ONLY")
        self.assertEqual(result["point"], [24, 38])
        self.assertIn("ordinary input admission remains required", result["authority"])

    def test_negative_classes_preserve_reason_and_have_no_point_or_authority(self):
        for reason in ("no_match_in_observed_set", "ambiguous_evidence",
                       "unavailable_evidence", "search_budget_exhausted"):
            with self.subTest(reason=reason):
                result = validate(decision("needs_decision", reason), READINESS)
                self.assertEqual(result["authority_class"], "NO_TARGET_AUTHORITY")
                self.assertEqual(result["diagnostic_reason"], reason)
                self.assertIsNone(result["point"])

    def test_negative_decision_cannot_smuggle_receipt_or_point(self):
        for mutation in (
            lambda value: value.update(receipt_index=1),
            lambda value: value.update(points=[{"x": 24, "y": 38}]),
            lambda value: value.update(point_space="source_observation_pixels"),
            lambda value: value.update(motion_model="surface_origin_translation"),
        ):
            with self.subTest(mutation=mutation):
                candidate = decision("needs_decision", "no_match_in_observed_set")
                mutation(candidate)
                with self.assertRaises(ValueError):
                    validate(candidate, READINESS)

    def test_positive_decision_must_cite_exact_observed_receipt(self):
        candidate = decision("target_reference", "matched", receipt_index=1,
            points=[{"x": 25, "y": 38}],
            point_space="source_observation_pixels",
            motion="surface_origin_translation")
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate(candidate, READINESS)
        candidate = copy.deepcopy(candidate)
        candidate["points"][0]["x"] = 24
        result = validate(candidate, READINESS)
        self.assertEqual(result["authority_class"], "TARGET_REFERENCE_ONLY")


if __name__ == "__main__":
    unittest.main()

"""Behavior tests with hand-derived expected labels and witnesses."""
import unittest

from modelchecker import build_artifact, diagnose


class ExpressibilityTests(unittest.TestCase):
    def test_opposite_labels_in_one_visible_fiber_stop(self):
        rows = [
            {"case_id": "x", "concrete": [True] * 4 + [False], "required": "FAIL"},
            {"case_id": "y", "concrete": [True] * 5, "required": "PASS"},
        ]
        result = diagnose(rows, [0, 1, 2, 3])
        self.assertEqual(result["status"], "ONTOLOGY_INSUFFICIENT")
        self.assertIsNone(result["decisions"])
        self.assertEqual(result["conflicting_classes"], [{
            "visible": [True] * 4, "members": ["x", "y"], "required": ["FAIL", "PASS"]}])

    def test_complete_vocabulary_separates_the_opposite_labels(self):
        rows = [
            {"case_id": "x", "concrete": [True] * 4 + [False], "required": "FAIL"},
            {"case_id": "y", "concrete": [True] * 5, "required": "PASS"},
        ]
        result = diagnose(rows, [0, 1, 2, 3, 4])
        self.assertEqual(result["status"], "EXPRESSIBLE")
        self.assertEqual(result["decisions"], [
            {"visible": [True] * 4 + [False], "required": "FAIL"},
            {"visible": [True] * 5, "required": "PASS"}])

    def test_same_label_aliases_are_not_false_insufficiency(self):
        rows = [
            {"case_id": "x", "concrete": [False] * 5, "required": "FAIL"},
            {"case_id": "y", "concrete": [False] * 4 + [True], "required": "FAIL"},
        ]
        self.assertEqual(diagnose(rows, [0, 1, 2, 3])["decisions"], [
            {"visible": [False] * 4, "required": "FAIL"}])

    def test_renamed_ids_cannot_remove_a_semantic_conflict(self):
        rows = [
            {"case_id": "opaque-z", "concrete": [True] * 4 + [False], "required": "FAIL"},
            {"case_id": "opaque-a", "concrete": [True] * 5, "required": "PASS"},
        ]
        result = diagnose(rows, [0, 1, 2, 3])
        self.assertEqual(result["status"], "ONTOLOGY_INSUFFICIENT")
        self.assertEqual(result["observable_class_count"], 1)
        self.assertIsNone(result["decisions"])

    def test_repeated_counterexample_does_not_split_a_fiber(self):
        rows = [
            {"case_id": "x", "concrete": [True] * 4 + [False], "required": "FAIL"},
            {"case_id": "y", "concrete": [True] * 5, "required": "PASS"},
            {"case_id": "z", "concrete": [True] * 4 + [False], "required": "FAIL"},
        ]
        result = diagnose(rows, [0, 1, 2, 3])
        self.assertEqual(result["status"], "ONTOLOGY_INSUFFICIENT")
        self.assertEqual(result["observable_class_count"], 1)
        self.assertEqual(result["conflicting_classes"][0]["members"], ["x", "y", "z"])

    def test_illegal_id_feature_and_integer_boolean_are_rejected(self):
        row = {"case_id": "x", "concrete": [True] * 5, "required": "PASS"}
        for vocabulary in ([0, 1, 2, 3, "case_id"], [0, True], [0, 0], [5], []):
            with self.subTest(vocabulary=vocabulary), self.assertRaises(ValueError):
                diagnose([row], vocabulary)
        row["concrete"][0] = 1
        with self.assertRaises(ValueError):
            diagnose([row], [0, 1, 2, 3])

    def test_full_model_retains_all_states_and_the_only_pass(self):
        output = build_artifact()
        self.assertEqual(len(output["rows"]), 32)
        self.assertEqual(output["rows"][30], {"case_id": "case_030", "concrete": [True] * 4 + [False], "required": "FAIL"})
        self.assertEqual(output["rows"][31], {"case_id": "case_031", "concrete": [True] * 5, "required": "PASS"})
        self.assertEqual(sum(row["required"] == "PASS" for row in output["rows"]), 1)
        self.assertEqual(output["restricted"]["observable_class_count"], 16)
        self.assertEqual(len(output["restricted"]["conflicting_classes"]), 1)
        self.assertEqual(output["complete"]["observable_class_count"], 32)
        self.assertEqual(len(output["complete"]["decisions"]), 32)

    def test_a_single_false_predicate_never_passes(self):
        output = build_artifact()
        for case_id in ("case_015", "case_023", "case_027", "case_029", "case_030"):
            row = next(row for row in output["rows"] if row["case_id"] == case_id)
            self.assertEqual(row["required"], "FAIL", case_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)

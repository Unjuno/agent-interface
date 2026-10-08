import json
import unittest

import audit_posthoc as audit


CONSTRUCTION_SEEDS = {"train": 600501, "calibration": 600502, "test": 600503}


class PosthocAuditConstruction(unittest.TestCase):
    def test_tuple_list_json_normalization(self):
        authored = {"feature_vector": (1, -1, 0), "labels": (0, 1), "nested": {"cues": ((1, 0),)}}
        normalized = json.loads(audit.json_bytes(authored))
        self.assertEqual(normalized, {"feature_vector": [1, -1, 0], "labels": [0, 1], "nested": {"cues": [[1, 0]]}})

    def test_small_seeded_reconstruction_is_deterministic_and_normalizes(self):
        left = audit.regenerate(CONSTRUCTION_SEEDS, per_block=20)
        right = audit.regenerate(CONSTRUCTION_SEEDS, per_block=20)
        self.assertEqual(audit.json_bytes(left), audit.json_bytes(right))
        normal_left = json.loads(audit.json_bytes(left))
        normal_right = json.loads(audit.json_bytes(right))
        self.assertEqual(normal_left, normal_right)
        self.assertEqual(left["train"]["mode_counts"], [400] * 5)
        self.assertEqual(len(left["calibration"]["rows"]), 100)
        self.assertEqual(len(left["test"]["rows"]), 100)
        self.assertEqual(left["seeds"], CONSTRUCTION_SEEDS)

    def test_all_corruption_controls_are_detected_after_normalization(self):
        reference = json.loads(audit.json_bytes(audit.regenerate(CONSTRUCTION_SEEDS, per_block=20)))
        changes = audit.corruptions(reference)
        self.assertEqual(len(changes), 16)
        for mutate in changes:
            altered = audit._mutated(reference, mutate)
            self.assertNotEqual(altered, reference)


if __name__ == "__main__":
    unittest.main()

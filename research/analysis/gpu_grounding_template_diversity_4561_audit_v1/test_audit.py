import copy
import unittest

from audit import ACCEPT_MIN, ARMS, HELDOUT, SEEDS, audit_data


def fixture():
    manifest_images = []
    cases = []
    all_families = tuple(f"family-{i:02d}" for i in range(1, 13))
    for fi, family in enumerate(all_families):
        for variant in range(4):
            field = [fi % 8, variant]
            submit = [fi % 8, (variant + 5) % 10]
            image_id = f"{family}/variant-{variant}"
            manifest_images.append({"image_id": image_id, "family_id": family,
                                   "field_cell": field, "submit_cell": submit,
                                   "field_point": [variant, fi], "submit_point": [variant + 1, fi]})
            if family not in HELDOUT:
                continue
            for seed in SEEDS:
                for arm in ARMS:
                    confidence = [0.2, 0.3]
                    wrong = arm == ARMS[0] and seed == SEEDS[0] and variant < 2
                    predicted = [[(field[0] + 1) % 8, field[1]], submit] if wrong else [field, submit]
                    cases.append({"seed": seed, "arm": arm, "image_id": image_id,
                                  "family_id": family, "target_cells": [field, submit],
                                  "target_points": [[variant, fi], [variant + 1, fi]],
                                  "predicted_cells": predicted, "exact_pair_correct": not wrong,
                                  "confidence": confidence, "accepted": False,
                                  "candidate_valid": False, "parsed_candidate": None,
                                  "accepted_wrong": False})
    return {"cases": cases}, {"images": manifest_images}


class FrozenTargetAuditTests(unittest.TestCase):
    def test_exact_fixture_passes_structural_population_and_label_checks(self):
        raw, manifest = fixture()
        result = audit_data(raw, manifest)
        self.assertEqual(result["status"], "PASS_TEMPLATE_DIVERSITY_SCOPED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["cases_checked"], 96)

    def test_self_consistent_target_tampering_is_rejected(self):
        raw, manifest = fixture()
        changed = raw["cases"][0]
        changed["target_cells"] = copy.deepcopy(changed["predicted_cells"])
        changed["exact_pair_correct"] = True
        result = audit_data(raw, manifest)
        self.assertIn("self-reported target cells disagree with frozen manifest", result["errors"])

    def test_family_and_image_substitution_are_rejected(self):
        raw, manifest = fixture()
        raw["cases"][0]["family_id"] = "family-12"
        raw["cases"][1]["image_id"] = "family-01/variant-0"
        errors = audit_data(raw, manifest)["errors"]
        self.assertIn("family ID disagrees with frozen image manifest", errors)
        self.assertIn("unknown or non-held-out image ID", errors)

    def test_seed_arm_and_target_point_substitution_are_rejected(self):
        raw, manifest = fixture()
        raw["cases"][0]["seed"] = 0
        raw["cases"][1]["arm"] = "unregistered_arm"
        raw["cases"][2]["target_points"][0][0] += 1
        errors = audit_data(raw, manifest)["errors"]
        self.assertIn("case outside exact frozen seed/arm/image population", errors)
        self.assertIn("self-reported target points disagree with frozen manifest", errors)

    def test_duplicate_missing_and_extra_cases_are_rejected(self):
        raw, manifest = fixture()
        raw["cases"].pop()
        raw["cases"].append(copy.deepcopy(raw["cases"][0]))
        errors = audit_data(raw, manifest)["errors"]
        self.assertIn("duplicate seed/arm/image case", errors)
        self.assertIn("missing or extra seed/arm/image cases", errors)

    def test_added_case_is_rejected(self):
        raw, manifest = fixture()
        extra = copy.deepcopy(raw["cases"][0])
        extra["seed"] = 999
        raw["cases"].append(extra)
        errors = audit_data(raw, manifest)["errors"]
        self.assertIn("case outside exact frozen seed/arm/image population", errors)
        self.assertIn("case cardinality is not exactly 96", errors)

    def test_confidence_and_acceptance_mutation_is_rejected(self):
        raw, manifest = fixture()
        raw["cases"][0]["confidence"] = [ACCEPT_MIN, 0.99]
        errors = audit_data(raw, manifest)["errors"]
        self.assertIn("accept/YIELD decision disagrees with frozen threshold", errors)
        self.assertIn("accepted proposal lacks validator evidence", errors)


if __name__ == "__main__":
    unittest.main()

import copy
import unittest

from audit import ARMS, FROZEN_UPDATES, SEEDS, audit_data, mutation_controls
from render import FAMILIES, source_family_sha256


def fixture():
    train = [f["id"] for f in FAMILIES[:8]]
    heldout = [f["id"] for f in FAMILIES[8:]]
    narrow = train[:2]
    metadata = [{"seed": seed, "arm": arm, "steps": FROZEN_UPDATES,
                 "train_family_ids": narrow if arm == ARMS[0] else train}
                for seed in SEEDS for arm in ARMS]
    cases = []
    for seed in SEEDS:
        for arm in ARMS:
            for family_index, spec in enumerate(FAMILIES[8:]):
                for variant in range(4):
                    target = [spec["field"], spec["submit"]]
                    # Narrow is 75% exact; broad is perfect on every held-out family.
                    correct = arm == ARMS[1] or variant != 0
                    predicted = copy.deepcopy(target if correct else [[7, 9], [7, 8]])
                    # Narrow errors abstain; every broad prediction is correct.
                    confidence = [0.9, 0.9] if correct else [0.6, 0.6]
                    cases.append({"seed": seed, "arm": arm, "family_id": spec["id"],
                                  "image_id": f"{spec['id']}/variant-{variant}",
                                  "target_cells": target, "predicted_cells": predicted,
                                  "confidence": confidence, "accepted": correct,
                                  "candidate_valid": correct,
                                  "parsed_candidate": {"fixture": True} if correct else None,
                                  "exact_pair_correct": correct,
                                  "accepted_wrong": False})
    return {"schema": "issue4561-template-diversity-formal-v1",
            "split": {"train_families": train, "heldout_families": heldout,
                      "narrow_families": narrow},
            "renderer": {"families": [{"family_id": f["id"],
                                        "family_sha256": source_family_sha256(f)} for f in FAMILIES]},
            "matrix": {"seed": SEEDS, "arms": ARMS, "updates_per_arm": FROZEN_UPDATES,
                       "batch": 16, "accept_min": 0.75},
            "metadata": metadata, "cases": cases}


class AuditTests(unittest.TestCase):
    def test_fixture_passes_scoped_gate(self):
        result = audit_data(fixture())
        self.assertEqual(result["status"], "PASS_TEMPLATE_DIVERSITY_SCOPED")
        self.assertEqual(result["cases_checked"], 96)
        self.assertAlmostEqual(result["absolute_delta"], 0.25)

    def test_fixture_mutations_are_rejected(self):
        outcomes = mutation_controls(fixture())
        self.assertEqual(len(outcomes), 7)
        self.assertTrue(all(outcomes.values()), outcomes)

    def test_failure_gate_is_reported_without_integrity_failure(self):
        raw = fixture()
        for row in raw["cases"]:
            if row["arm"] == ARMS[1]:
                row["predicted_cells"] = [[7, 9], [7, 8]]
                row["exact_pair_correct"] = False
                row["accepted"] = False
                row["candidate_valid"] = False
                row["parsed_candidate"] = None
                row["confidence"] = [0.6, 0.6]
                row["accepted_wrong"] = False
        result = audit_data(raw)
        self.assertEqual(result["status"], "HOLD_OR_FAIL_FROZEN_GATES_NOT_MET")


if __name__ == "__main__":
    unittest.main()

import unittest
from copy import deepcopy
import study
import audit

CONSTRUCTION_TRAIN = (415001, 415002, 415003)
CONSTRUCTION_TEST = (415011, 415012, 415013)


class ConstructionTests(unittest.TestCase):
    def test_formal_regeneration_is_exact(self):
        first = study.generate_rows(415011, 64, split="heldout", block="SINGLE_MISSING")
        self.assertEqual(first, study.generate_rows(415011, 64, split="heldout", block="SINGLE_MISSING"))

    def test_support_and_heldout_ids_are_separate(self):
        for i, seed in enumerate(CONSTRUCTION_TEST):
            support = study.generate_rows(CONSTRUCTION_TRAIN[i], study.TRAIN_PER_MODE,
                                          split="support", block="COMPLETE")
            heldout = study.generate_rows(seed, 64, split="heldout", block="SINGLE_MISSING")
            self.assertEqual(len({r["row_id"] for r in support}), len(support))
            self.assertTrue({r["row_id"] for r in support}.isdisjoint(r["row_id"] for r in heldout))

    def test_strata_are_balanced_and_masks_are_explicit(self):
        rows = study.generate_rows(415021, 64, split="heldout", block="SINGLE_MISSING")
        self.assertEqual(set(r["mode"] for r in rows), set(study.MODES))
        self.assertEqual([sum(r["mode"] == m for r in rows) for m in study.MODES], [64] * 5)
        self.assertTrue(all(sum(v is None for v in r["features"]) >= 1 for r in rows))

    def test_controls_abstain_and_full_prototypes_agree(self):
        train = study.generate_rows(415001, study.TRAIN_PER_MODE, split="support", block="COMPLETE")
        direct = study.fit(train, tuple(sorted(set(study.DISPOSITION.values()))), label_key="expected")
        mode = study.fit(train, study.MODES, label_key="mode")
        controls = study.generate_controls(415011)
        for row in controls:
            result = study.predict(direct, mode, row)
            if row["mode"] == "UNKNOWN":
                self.assertEqual(result["direct"]["action"], "YIELD")
                self.assertEqual(result["mode"]["action"], "YIELD")
            else:
                self.assertEqual(result["direct"]["action"], row["expected"])
                self.assertEqual(result["mode"]["action"], row["expected"])

    def test_independent_audit_accepts_exact_generated_fixture(self):
        raw = study.make_formal(CONSTRUCTION_TRAIN, CONSTRUCTION_TEST)
        result = audit.audit(raw, CONSTRUCTION_TRAIN, CONSTRUCTION_TEST)
        self.assertEqual(result["errors"], [])

    def test_independent_audit_rejects_prediction_corruption(self):
        raw = study.make_formal(CONSTRUCTION_TRAIN, CONSTRUCTION_TEST)
        broken = deepcopy(raw)
        broken["seeds"][0]["blocks"][0]["rows"][0]["predictions"]["direct"]["action"] = "REBIND"
        result = audit.audit(broken, CONSTRUCTION_TRAIN, CONSTRUCTION_TEST)
        self.assertTrue(any(error.startswith("prediction:") for error in result["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

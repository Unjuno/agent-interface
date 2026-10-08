import copy
import json
import unittest
from pathlib import Path

import audit
import candidate

DATA = json.loads((Path(__file__).parent / "fixture.json").read_text())
OUTPUT = candidate.run(DATA)


class ArtifactValueTests(unittest.TestCase):
    def test_sunk_spend_only_is_invariant(self):
        self.assertTrue(OUTPUT["pairs"]["sunk_only"]["forward_equivalent"])
        self.assertEqual(OUTPUT["cards"]["baseline_low_sunk"]["choice"], "SWITCH")
        self.assertEqual(OUTPUT["cards"]["same_forward_high_sunk"]["choice"], "SWITCH")

    def test_verified_artifact_can_rationally_change_choice(self):
        card = next(c for c in DATA["cards"] if c["id"] == "verified_reusable_artifact")
        self.assertEqual(card["artifact_applicability"], "verified")
        self.assertEqual(OUTPUT["cards"][card["id"]]["values"], {"CONTINUE": "8", "SWITCH": "5"})
        self.assertEqual(OUTPUT["cards"][card["id"]]["choice"], "CONTINUE")

    def test_stale_artifact_does_not_earn_forward_value(self):
        card = next(c for c in DATA["cards"] if c["id"] == "stale_nonapplicable_artifact")
        self.assertEqual(card["artifact_applicability"], "invalid")
        self.assertEqual(OUTPUT["cards"][card["id"]]["choice"], "SWITCH")

    def test_auditor_reconstructs_all_cards_and_pairs(self):
        result = audit.audit(DATA, OUTPUT)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual((result["cards_reconstructed"], result["pairs_reconstructed"]), (4, 3))

    def test_auditor_detects_planted_artifact_value_inflation(self):
        corrupted = copy.deepcopy(OUTPUT)
        corrupted["cards"]["stale_nonapplicable_artifact"]["choice"] = "CONTINUE"
        self.assertEqual(audit.audit(DATA, corrupted)["status"], "FAIL")

    def test_auditor_detects_planted_applicability_and_pair_label_changes(self):
        corrupted = copy.deepcopy(OUTPUT)
        corrupted["pairs"]["sunk_only"]["forward_equivalent"] = False
        corrupted["pairs"]["stale_artifact_is_not_future_value"]["accepted_as_matched"] = False
        self.assertEqual(audit.audit(DATA, corrupted)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()

import copy
import json
import unittest
from pathlib import Path

import audit
import candidate


HERE = Path(__file__).resolve().parent


class IndependentAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
        cls.raw = candidate.run(cls.fixture)

    def test_unmodified_candidate_passes_reconstruction(self):
        result = audit.validate(self.fixture, self.raw)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["cases_reconstructed"], 5)

    def test_five_frozen_mutations_are_rejected(self):
        mutations = []
        row_by_id = {row["case_id"]: row for row in self.raw["cases"]}

        false_recover = copy.deepcopy(self.raw)
        row_by_id = {row["case_id"]: row for row in false_recover["cases"]}
        row_by_id["spurious_recovery_unsafe_only_separator"]["cegar"]["verdict"] = "RECOVERABLE"
        row_by_id["spurious_recovery_unsafe_only_separator"]["cegar"]["policy"] = {"action": "go", "branches": []}
        mutations.append(false_recover)

        unsafe_predicate = copy.deepcopy(self.raw)
        {r["case_id"]: r for r in unsafe_predicate["cases"]}["spurious_recovery_unsafe_only_separator"]["cegar"]["predicates_used"] = ["p_secret"]
        mutations.append(unsafe_predicate)

        wrong_refinement = copy.deepcopy(self.raw)
        row = {r["case_id"]: r for r in wrong_refinement["cases"]}["spurious_loss_safe_separator"]
        row["cegar"]["predicates_used"] = ["p_phase"]
        row["cegar"]["refinements"] = [{"added": "p_phase", "verdict": "RECOVERABLE"}]
        mutations.append(wrong_refinement)

        hidden_state = copy.deepcopy(self.raw)
        row = {r["case_id"]: r for r in hidden_state["cases"]}["action_equivalent_aliases"]
        row["cegar"]["policy"] = {"action": "f", "branches": []}
        mutations.append(hidden_state)

        wrong_hash = copy.deepcopy(self.raw)
        wrong_hash["fixture_sha256"] = "0" * 64
        mutations.append(wrong_hash)

        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assertFalse(audit.validate(self.fixture, mutation)["passed"])


if __name__ == "__main__":
    unittest.main()

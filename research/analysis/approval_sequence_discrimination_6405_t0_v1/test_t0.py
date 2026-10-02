import copy
import json
import unittest
from pathlib import Path

from auditor import audit, mutation_controls
from candidate import build_raw


ROOT = Path(__file__).resolve().parent


class ApprovalSequenceT0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.raw = build_raw(cls.fixture)

    def test_exact_sequence_and_all_display_arms(self):
        self.assertEqual([], audit(self.raw, self.fixture))
        self.assertEqual({"A": 9, "B": 9, "C": 9}, {k: len(v) for k, v in self.raw["arms"].items()})

    def test_source_bound_change_highlights(self):
        self.assertEqual(["recipient", "target", "effect", "scope"], self.raw["arms"]["B"][5]["highlight_fields"])
        self.assertEqual(["target", "effect", "scope", "expiry"], self.raw["arms"]["B"][8]["highlight_fields"])

    def test_batch_keeps_individual_scopes_and_excludes_consequential_changes(self):
        batch = [r for r in self.raw["arms"]["C"] if r["batch_id"]]
        self.assertEqual(["R01", "R02", "R03", "R04", "R05"], [r["request_id"] for r in batch])
        self.assertTrue(all(r["receipt"]["request_digest"] == r["request_digest"] for r in batch))
        self.assertIsNone(self.raw["arms"]["C"][5]["batch_id"])

    def test_denial_never_mints_receipt(self):
        self.assertTrue(all(r["receipt"] is None for arm in self.raw["arms"].values() for r in arm if r["request_id"] == "R08"))

    def test_late_scope_change_gets_fresh_digest(self):
        for arm in self.raw["arms"].values():
            old, changed = arm[0], arm[8]
            self.assertEqual("R01", changed["supersedes_request_id"])
            self.assertEqual(old["request_digest"], changed["supersedes_digest"])
            self.assertNotEqual(old["request_digest"], changed["request_digest"])
            self.assertEqual(changed["request_digest"], changed["receipt"]["request_digest"])

    def test_all_frozen_corruptions_rejected(self):
        self.assertEqual({"omitted_field": True, "swapped_recipient": True, "stale_highlight": True,
                          "overbroad_batch": True, "prior_receipt_reuse": True},
                         mutation_controls(self.raw, self.fixture))

    def test_oracle_rejects_one_field_mutations(self):
        mutations = []
        bad = copy.deepcopy(self.raw); bad["arms"]["A"][0]["fields"].pop("expiry"); mutations.append(bad)
        bad = copy.deepcopy(self.raw); bad["arms"]["A"][0]["fields"]["recipient"] = "attacker"; mutations.append(bad)
        bad = copy.deepcopy(self.raw); bad["arms"]["B"][1]["highlight_fields"] = ["effect"]; mutations.append(bad)
        for mutated in mutations:
            self.assertTrue(audit(mutated, self.fixture))


if __name__ == "__main__":
    unittest.main()

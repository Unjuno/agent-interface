import json
import unittest

import auditor
import candidate


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("fixture.json", encoding="utf-8") as f:
            cls.fixture = json.load(f)
        cls.result = candidate.run(cls.fixture)
        cls.oracle = auditor.oracle(cls.fixture)

    def test_candidate_matches_independent_oracle(self):
        self.assertEqual({k: v for k, v in self.result.items() if k != "schema"}, self.oracle)

    def test_all_strict_orders_are_in_fixture_and_oracle(self):
        self.assertEqual(len(self.fixture["preference_domain"]), 6)
        self.assertEqual(len({tuple(x) for x in self.fixture["preference_domain"]}), 6)
        self.assertTrue(all(len(s["identified_orders"]) == 3 for s in self.oracle["scopes"]))

    def test_only_complete_verified_direct_choices_are_admitted(self):
        self.assertEqual(self.result["admissible_event_ids"], ["e01", "e08a", "e08b", "e09a", "e09b"])

    def test_context_and_version_are_isolated(self):
        scopes = {tuple(s["scope"][3:]): s for s in self.result["scopes"]}
        self.assertTrue({("delivery", "v1"), ("appearance", "v1"),
                         ("preferences", "v1"), ("preferences", "v2")} <= set(scopes))
        self.assertNotEqual(scopes[("preferences", "v1")]["event_ids"],
                            scopes[("preferences", "v2")]["event_ids"])

    def test_mutations_fail_closed_or_split_scope(self):
        self.assertEqual([m["result"] for m in self.result["mutations"]],
                         ["NO_IDENTIFIED_COMPARISON"] * 4 + ["SEPARATE_SCOPE"])


if __name__ == "__main__":
    unittest.main()

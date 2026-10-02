import unittest

from audit import audit, enumerate_contract, validate
from candidate import build_raw
from fixture import START, classify, reachable


class PrefixStabilityTests(unittest.TestCase):
    def test_reachable_graph_has_unique_start(self):
        states = reachable()
        self.assertIn(START, states)
        self.assertGreater(len(states), 100)

    def test_candidate_and_independent_state_sets_match(self):
        self.assertTrue(validate(build_raw()))

    def test_decisive_negative_finalizes_with_pending_obligations(self):
        row = next(r for r in build_raw()["rows"] if r["state"].get("mandatory_fail") and r["state"].get("sealed"))
        self.assertEqual(row["classification"], "STABLE_FINAL_FAIL")
        self.assertTrue(row["pending_obligations"])

    def test_open_source_frontier_never_passes(self):
        row = next(r for r in build_raw()["rows"] if r["state"].get("mandatory_all_pass") and not r["state"].get("source_a_closed"))
        self.assertNotEqual(row["classification"], "STABLE_FINAL_PASS")
        self.assertIn("source_a_completion", row["pending_obligations"])

    def test_timeout_is_not_source_close(self):
        row = next(r for r in build_raw()["rows"] if r["state"].get("source_a_timeout") and not r["state"].get("source_a_closed"))
        self.assertIn("source_a_completion", row["pending_obligations"])

    def test_invalidated_generation_resets_current_evidence(self):
        self.assertTrue(any(s[0] == 1 and s[2] and not s[3] and not s[4] for s in reachable()))

    def test_unknown_contract_is_unknown(self):
        row = next(r for r in build_raw()["rows"] if r["state"] == {"contract_known": False})
        self.assertEqual(row["classification"], "UNKNOWN")

    def test_independent_enumerator_reaches_same_number_of_states(self):
        self.assertEqual(len(enumerate_contract()) + 1, len(build_raw()["rows"]))

    def test_required_mutations_are_rejected(self):
        raw = build_raw()
        self.assertTrue(validate(raw))
        result = audit(raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertTrue(all(result["mutation_controls_rejected"].values()))
        altered = raw.copy(); altered["rows"] = raw["rows"][:-1]
        self.assertFalse(validate(altered))


if __name__ == "__main__": unittest.main()

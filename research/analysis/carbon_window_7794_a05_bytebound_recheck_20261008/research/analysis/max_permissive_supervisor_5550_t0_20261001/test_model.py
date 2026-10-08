import unittest

import audit
import model


class SupervisorModelTests(unittest.TestCase):
    def test_candidate_and_independent_oracle_agree(self):
        result = model.run()
        checked = audit.audit(result)
        self.assertEqual(checked["status"], "PASS_T0_SYNTHETIC_SCOPE", checked)

    def test_synthesized_never_enters_unsafe_state(self):
        rows = model.explore("synthesized")
        self.assertFalse([row for row in rows if row["unsafe"]])

    def test_greedy_allow_list_exposes_both_safety_faults(self):
        rows = model.explore("greedy_allow_list")
        dests = {row["destination"] for row in rows}
        self.assertIn("UNSAFE_STALE_COMMIT", dests)
        self.assertIn("UNSAFE_DOUBLE_EFFECT", dests)

    def test_synthesis_recovers_after_focus_and_target_change(self):
        rows = model.explore("synthesized")
        traces = {tuple(row["trace"]) for row in rows}
        self.assertIn(("FOCUS_LOST", "REACQUIRE", "ACT", "COMMIT"), traces)
        self.assertIn(("ACT", "TARGET_CHANGED", "REACQUIRE", "ACT", "COMMIT"), traces)

    def test_uncontrollable_close_is_terminal_not_authorized_completion(self):
        rows = model.explore("synthesized")
        blocked = [row for row in rows if row["blocked"]]
        self.assertTrue(blocked)
        self.assertTrue(all(not row["completed"] for row in blocked))

    def test_oracle_rejects_removed_uncontrollable_transition(self):
        raw = model.run()
        raw["rows"] = [r for r in raw["rows"] if r["event"] != "WINDOW_CLOSE"]
        self.assertNotEqual(audit.audit(raw)["status"], "PASS_T0_SYNTHETIC_SCOPE")

    def test_oracle_rejects_added_unsafe_supervisor_edge(self):
        raw = model.run()
        raw["synthesized_enabled"]["STALE"].append("COMMIT")
        self.assertNotEqual(audit.audit(raw)["status"], "PASS_T0_SYNTHETIC_SCOPE")


if __name__ == "__main__":
    unittest.main()

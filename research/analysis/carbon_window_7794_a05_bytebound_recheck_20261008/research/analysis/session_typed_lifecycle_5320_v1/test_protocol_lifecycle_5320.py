import unittest

from protocol_lifecycle_5320 import run


POLICIES = ("CONVENTION_ONLY", "RUNTIME_AUTOMATON", "LINEAR_PROTOCOL", "MULTIPARTY_PROTOCOL")


class LifecycleProtocolTests(unittest.TestCase):
    def test_release_before_acquire_is_rejected_by_monitor(self):
        trace = [("owner", "release", 0)]
        self.assertTrue(run(trace, "CONVENTION_ONLY")["accepted"][0])
        for policy in POLICIES[1:]:
            self.assertFalse(run(trace, policy)["accepted"][0])

    def test_post_expiry_commit_is_rejected(self):
        trace = [("owner", "acquire", 0), ("broker", "prepare", 1),
                 ("owner", "expire", 2), ("broker", "begin_commit", 3)]
        for policy in POLICIES[1:]:
            self.assertEqual([True, True, True, False], run(trace, policy)["accepted"])

    def test_unknown_outcome_can_reconcile_then_release_without_claim(self):
        trace = [("owner", "acquire", 0), ("broker", "prepare", 1),
                 ("broker", "begin_commit", 2), ("verifier", "effect_unknown", 3),
                 ("verifier", "resolve_absent", 4), ("owner", "release", 5)]
        for policy in POLICIES[1:]:
            got = run(trace, policy)
            self.assertTrue(all(got["accepted"]))
            self.assertEqual("RELEASED", got["final_state"])
            self.assertFalse(got["effect_claim_created"])
            self.assertFalse(got["authority_created"])

    def test_duplicate_linear_capability_is_rejected(self):
        trace = [("owner", "acquire", 0), ("broker", "prepare", 0)]
        self.assertEqual([True, True], run(trace, "RUNTIME_AUTOMATON")["accepted"])
        self.assertEqual([True, False], run(trace, "LINEAR_PROTOCOL")["accepted"])

    def test_wrong_role_rejected_only_by_multiparty_projection(self):
        trace = [("owner", "acquire", 0), ("owner", "prepare", 1)]
        self.assertTrue(run(trace, "RUNTIME_AUTOMATON")["accepted"][1])
        self.assertFalse(run(trace, "MULTIPARTY_PROTOCOL")["accepted"][1])

    def test_unknown_event_fails_closed_and_does_not_change_state(self):
        for policy in POLICIES:
            got = run([("planner", "invent_authority", 0)], policy)
            self.assertFalse(got["accepted"][0])
            self.assertEqual("OFFERED", got["final_state"])
            self.assertFalse(got["authority_created"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

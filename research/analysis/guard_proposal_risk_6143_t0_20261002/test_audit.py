import unittest
from fractions import Fraction

from audit import audit
from simulator import analyze


FIXTURE = {
    "schema": "guard-proposal-risk-fixture-v1",
    "max_proposals_per_episode": 2,
    "worlds": [{"true_harmful": True, "weight": "3/4"}, {"true_harmful": False, "weight": "1/4"}],
    "guard_confusion": {"true_positive_reject": "3/4", "false_positive_reject": "1/4"},
    "policies": {"conservative_risky_probability": "1/4", "compensated_risky_probability": "3/4", "protective_risky_probability": "0"},
    "harm_materiality_margin": "1/10",
}


def jsonable(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    return value


class IndependentAuditTests(unittest.TestCase):
    def test_independent_replay_accepts_candidate_and_planted_controls(self):
        result = audit(FIXTURE, jsonable(analyze(FIXTURE)))
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["replayed_world_weight"], "1")
        self.assertTrue(result["compensation_control_caught"])
        self.assertTrue(result["null_control_not_flagged"])
        self.assertTrue(result["protective_control_not_flagged"])

    def test_independent_audit_rejects_candidate_harm_mutation(self):
        candidate = jsonable(analyze(FIXTURE))
        candidate["cells"]["guard_induced_aggressive_guard_on"]["task_harm_fraction"] = "0"
        result = audit(FIXTURE, candidate)
        self.assertEqual(result["status"], "FAIL_CANDIDATE_MISMATCH")
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()

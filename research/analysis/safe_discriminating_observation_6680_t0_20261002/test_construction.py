import copy
import json
import unittest

import auditor
import candidate


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(candidate.FIXTURE.read_text())
        self.oracle = json.loads((candidate.FIXTURE.parent / "oracle.json").read_text())

    def test_positive_and_negative_controls(self):
        raw = candidate.run(self.fixture)
        result = auditor.audit(raw, self.fixture, self.oracle)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED", result)
        self.assertEqual(result["rows"], 20)

    def test_response_label_swap_is_detected(self):
        fx = copy.deepcopy(self.fixture)
        fx["probe"]["response_sets"]["H_OBSERVATION"], fx["probe"]["response_sets"]["H_DYNAMICS"] = (
            fx["probe"]["response_sets"]["H_DYNAMICS"], fx["probe"]["response_sets"]["H_OBSERVATION"]
        )
        result = auditor.audit(candidate.run(fx), fx, self.oracle)
        self.assertEqual(result["status"], "FAIL_AUDIT")

    def test_oracle_corruption_is_detected_by_decision_gate(self):
        bad_oracle = copy.deepcopy(self.oracle)
        bad_oracle["hidden_worlds"]["obs-path-identifiable"]["correct_recovery"] = "reset"
        result = auditor.audit(candidate.run(self.fixture), self.fixture, bad_oracle)
        self.assertIn("diagnostic policy failed an identifiable world", result["errors"])

    def test_ineligible_probe_fails_closed(self):
        fx = copy.deepcopy(self.fixture)
        action, observations = candidate.diagnose(fx, fx["cases"][3])
        self.assertIsNone(action)
        self.assertEqual(observations, 0)


if __name__ == "__main__":
    unittest.main()

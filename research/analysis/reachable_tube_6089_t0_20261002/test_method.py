import json
import unittest
from pathlib import Path

import audit
import candidate


CASES = json.loads((Path(__file__).with_name("cases.json")).read_text())["cases"]


class MethodConstructionTests(unittest.TestCase):
    def setUp(self):
        self.rows = candidate.run(CASES)

    def test_fixture_discriminators(self):
        rows = {row["case_id"]: row for row in self.rows}
        self.assertEqual(rows["narrow_corridor"]["robust_max_horizon"], 4)
        self.assertEqual(rows["wide_initial_uncertainty"]["robust_max_horizon"], 2)
        self.assertGreater(rows["safe_long_corridor"]["selected_horizon"], 1)
        self.assertEqual(rows["near_boundary"]["selected_horizon"], 0)
        self.assertEqual(rows["moving_forbidden_boundary"]["robust_max_horizon"], 2)
        self.assertEqual(rows["invalidated_target"]["outcome"], "YIELD_INVALIDATED_SOURCE")
        self.assertEqual(rows["zero_slack_release"]["selected_horizon"], 0)
        self.assertEqual(rows["disturbance_bound_violation_stress"]["stress"]["disposition"], "OUT_OF_ENVELOPE_NOT_CERTIFIED")
        self.assertFalse(rows["disturbance_bound_violation_stress"]["stress"]["safe"])

    def test_independent_recursive_oracle_accepts_candidate(self):
        self.assertEqual(audit.audit(CASES, self.rows), {"status": "PASS_METHOD_SCOPED", "errors": []})

    def test_corruptions_rejected(self):
        mutations = []
        altered = json.loads(json.dumps(self.rows)); altered[0]["selected_horizon"] += 1; mutations.append(altered)
        altered = json.loads(json.dumps(self.rows)); altered[0]["horizon_table"].pop(); mutations.append(altered)
        altered = json.loads(json.dumps(self.rows)); altered[5]["outcome"] = "ROBUST_HORIZON"; altered[5]["selected_horizon"] = 4; mutations.append(altered)
        altered = json.loads(json.dumps(self.rows)); altered[-1]["stress"]["disposition"] = "IN_ENVELOPE_CHECK"; mutations.append(altered)
        altered = json.loads(json.dumps(self.rows)); altered.pop(2); mutations.append(altered)
        self.assertEqual(len(mutations), 5)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertEqual(audit.audit(CASES, mutation)["status"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)

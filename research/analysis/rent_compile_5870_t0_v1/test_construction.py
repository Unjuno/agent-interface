import json
import unittest

import audit
import candidate


FIXTURE_BYTES = open("fixtures.json", "rb").read()
FIXTURE = json.loads(FIXTURE_BYTES)


class ConstructionTests(unittest.TestCase):
    def test_grid_and_prefix_bound_are_fixed(self):
        self.assertEqual(len(FIXTURE["configurations"]), 6)
        self.assertEqual(FIXTURE["max_prefix"], 30)

    def test_online_threshold_does_not_use_sequence_horizon(self):
        config = FIXTURE["configurations"][0]
        rows = candidate.simulate(config, 8)
        self.assertEqual([r["action"] for r in rows[:5]], ["DIRECT"] * 5)
        self.assertEqual(rows[5]["action"], "COMPILE_THEN_GUARDED")
        self.assertEqual(rows[5]["observed_direct_premium"], 30)

    def test_unqualified_and_non_saving_stay_direct(self):
        for config in (FIXTURE["configurations"][4], FIXTURE["configurations"][5]):
            rows = candidate.simulate(config, 30)
            self.assertTrue(all(row["action"] == "DIRECT" for row in rows))
            self.assertTrue(all(row["compile_charge"] == 0 for row in rows))

    def test_independent_oracle_reconstructs_candidate_rows(self):
        rows = []
        for config in FIXTURE["configurations"]:
            rows.extend(candidate.simulate(config, FIXTURE["max_prefix"]))
        offset = 0
        for config in FIXTURE["configurations"]:
            expected = list(audit.expected_rows(config, FIXTURE["max_prefix"]))
            self.assertEqual(rows[offset:offset + FIXTURE["max_prefix"]], expected)
            offset += FIXTURE["max_prefix"]

    def test_audit_corruption_controls_reject(self):
        header = {"type": "header", "schema": "rent-compile-5870-raw-v1",
                  "allocation": audit.ALLOCATION,
                  "fixture_sha256": __import__("hashlib").sha256(FIXTURE_BYTES).hexdigest(),
                  "policy": FIXTURE["policy"]}
        rows = [header]
        for config in FIXTURE["configurations"]:
            rows.extend(candidate.simulate(config, FIXTURE["max_prefix"]))
        result = audit.audit(FIXTURE, FIXTURE_BYTES, rows)
        self.assertTrue(all(result["corruption_controls"].values()))
        self.assertEqual(result["corruption_controls_rejected"], 4)


if __name__ == "__main__":
    unittest.main()

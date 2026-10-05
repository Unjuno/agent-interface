import json
import tempfile
import unittest
from pathlib import Path

import candidate
import auditor


ROOT = Path(__file__).resolve().parent


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((ROOT / "protocol.json").read_text())

    def test_seed_sets_are_disjoint_and_sized(self):
        p = self.protocol
        self.assertEqual(80, len(p["search_seeds"]))
        self.assertEqual(200, len(p["confirmation_seeds"]))
        self.assertFalse(set(p["search_seeds"]) & set(p["confirmation_seeds"]))

    def test_authority_and_release_are_nonremovable(self):
        p = self.protocol
        for event in ("AUTH", "RELEASE"):
            trace = list(p["base_trace"])
            trace.remove(event)
            self.assertFalse(candidate.safe(trace))

    def test_competing_failure_shares_exit_code_but_not_fingerprint(self):
        out = candidate.run(["AUTH", "SETUP", "CORE_B", "DECOY", "RELEASE"], "control", "lane")
        self.assertEqual("COMPETING:BAD_ROUTE:EXIT42", out)
        self.assertNotEqual("TARGET:LEASE_TIMEOUT:EXIT42", out)

    def test_confidence_bounds_order(self):
        low = candidate.cp_lower(72, 80, 0.01)
        high = candidate.cp_upper(72, 80, 0.01)
        self.assertLessEqual(low, 0.9)
        self.assertGreaterEqual(high, 0.9)

    def test_reducers_have_independent_holdout(self):
        p = self.protocol
        for method in ("A_SINGLE", "B_FIXED", "C_SEQUENTIAL"):
            result = candidate.reduce(p["base_trace"], p, method)
            self.assertTrue(candidate.safe(result["final_trace"]))

    def test_query_budget_and_holdout_signal(self):
        p = self.protocol
        fixed = candidate.reduce(p["base_trace"], p, "B_FIXED")
        sequential = candidate.reduce(p["base_trace"], p, "C_SEQUENTIAL")
        self.assertLess(sequential["query_count"], fixed["query_count"])

    def test_end_to_end_raw_only_audit_and_expected_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "candidate.json"
            audit_path = Path(temp) / "audit.json"
            candidate.main(str(ROOT / "protocol.json"), str(raw))
            audit_result = auditor.run(str(ROOT / "protocol.json"), str(raw), str(audit_path))
            self.assertEqual("PASS_METHOD_SCOPED", audit_result["disposition"])
            self.assertTrue(audit_result["mutation_checks"]["authority_drop"])
            self.assertTrue(audit_result["mutation_checks"]["release_drop"])
            self.assertTrue(audit_result["mutation_checks"]["same_exit_code_competitor"])
            self.assertTrue(audit_result["mutation_checks"]["missing_row_rejected"])
            self.assertLess(audit_result["sequential_queries"], audit_result["fixed_queries"])
            self.assertTrue(all(v >= .99 for v in audit_result["interval_coverage_grid"]["sequential_by_n"].values()))
            self.assertFalse(audit_result["heldout_noninferiority_by_method"]["A_SINGLE"])
            self.assertTrue(audit_result["heldout_noninferiority_by_method"]["C_SEQUENTIAL"])


if __name__ == "__main__":
    unittest.main()

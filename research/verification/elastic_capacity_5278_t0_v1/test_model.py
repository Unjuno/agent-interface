import base64
import json
import os
import unittest

from simulator import POLICIES, load_workloads, run_all
from auditor import audit, corruption_controls

WORKLOADS = load_workloads()


class CapacityT0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = run_all(WORKLOADS)
        cls.by_key = {(r["case_id"], r["policy"]): r for r in cls.raw["cases"]}

    def test_full_frozen_case_policy_matrix(self):
        self.assertEqual(len(self.raw["cases"]), 21)
        self.assertEqual(set(self.by_key), {
            (c["case_id"], p) for c in WORKLOADS["cases"] for p in POLICIES
        })

    def test_independent_audit_accepts_clean_control(self):
        self.assertEqual(audit(self.raw, WORKLOADS), [])

    def test_elastic_burst_gain_and_idle_cost_gate(self):
        small = self.by_key[("short_burst", "FIXED_SMALL")]["metrics"]
        elastic = self.by_key[("short_burst", "ELASTIC_DEADLINE_FRESHNESS_AWARE")]["metrics"]
        self.assertGreater(elastic["completed"], small["completed"])
        fixed_large_idle = sum(self.by_key[(c, "FIXED_LARGE")]["metrics"]["idle_ms"]
                               for c in ("short_burst", "sustained_burst"))
        elastic_idle = sum(self.by_key[(c, "ELASTIC_DEADLINE_FRESHNESS_AWARE")]["metrics"]["idle_ms"]
                           for c in ("short_burst", "sustained_burst"))
        self.assertLessEqual(elastic_idle, 0.75 * fixed_large_idle)

    def test_stale_work_never_completes(self):
        for policy in POLICIES:
            row = self.by_key[("stale_before_service", policy)]
            self.assertEqual(row["metrics"]["completed"], 0)
            self.assertEqual(row["plan_outcome"], "UNCERTAIN")
            self.assertGreater(row["metrics"]["stale_or_infeasible_before_execution"], 0)

    def test_startup_late_work_is_rejected_before_execution(self):
        for policy in POLICIES:
            row = self.by_key[("startup_too_late", policy)]
            self.assertEqual(row["attempts"], [])
            self.assertEqual(row["metrics"]["infeasible_before_start"], 6)
            self.assertEqual(row["plan_outcome"], "UNCERTAIN")

    def test_scale_in_does_not_terminate_active_job(self):
        row = self.by_key[("scale_in_while_active", "ELASTIC_DEADLINE_FRESHNESS_AWARE")]
        long_end = next(a["end_ms"] for a in row["attempts"] if a["job_id"] == "scalein-2")
        stop_times = [w["stop_start_ms"] for w in row["workers"] if w["stop_start_ms"] is not None]
        self.assertTrue(any(t < long_end for t in stop_times))
        self.assertEqual(row["jobs"][2]["status"], "COMPLETED")

    def test_result_semantics_are_policy_invariant(self):
        for case in WORKLOADS["cases"]:
            observed = {}
            for policy in POLICIES:
                row = self.by_key[(case["case_id"], policy)]
                observed[policy] = {j["job_id"]: j["result_sha256"]
                                    for j in row["jobs"] if j["status"] == "COMPLETED"}
            ids = set().union(*(set(v) for v in observed.values()))
            for jid in ids:
                digests = {observed[p][jid] for p in POLICIES if jid in observed[p]}
                self.assertEqual(len(digests), 1)

    def test_all_five_raw_corruptions_are_rejected(self):
        controls = corruption_controls(self.raw, WORKLOADS)
        self.assertEqual(len(controls), 5)
        self.assertTrue(all(c["rejected"] for c in controls))


if __name__ == "__main__":
    unittest.main(verbosity=2)

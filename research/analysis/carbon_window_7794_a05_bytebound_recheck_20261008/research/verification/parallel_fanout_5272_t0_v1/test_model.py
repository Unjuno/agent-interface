import unittest
from pathlib import Path

from simulator import POLICIES, load_workloads, run_all
from audit import audit, corruption_controls

WORKLOADS = load_workloads()


class FanoutT0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = run_all(WORKLOADS)
        cls.rows = {(r["case_id"], r["policy"]): r for r in cls.raw["cases"]}

    def test_complete_case_policy_matrix(self):
        self.assertEqual(len(self.raw["cases"]), len(WORKLOADS["cases"]) * len(POLICIES))
        self.assertEqual(set(self.rows), {
            (case["case_id"], policy)
            for case in WORKLOADS["cases"] for policy in POLICIES
        })

    def test_independent_fanout_meets_latency_gate(self):
        serial = self.rows[("independent", "SERIAL_VERIFIERS")]
        parallel = self.rows[("independent", "PARALLEL_FANOUT")]
        self.assertLessEqual(parallel["decision_ready_ms"] * 4, serial["decision_ready_ms"] * 3)

    def test_oracle_decisions_and_semantic_results(self):
        for case in WORKLOADS["cases"]:
            left = self.rows[(case["case_id"], "SERIAL_VERIFIERS")]
            right = self.rows[(case["case_id"], "PARALLEL_FANOUT")]
            self.assertEqual(left["decision"], case["expected_decision"], case["case_id"])
            self.assertEqual(right["decision"], case["expected_decision"], case["case_id"])

    def test_missing_mandatory_never_passes(self):
        for key in [("mandatory_deadline", "SERIAL_VERIFIERS"),
                    ("budget_saturation", "SERIAL_VERIFIERS"),
                    ("mandatory_deadline", "PARALLEL_FANOUT"),
                    ("budget_saturation", "PARALLEL_FANOUT")]:
            self.assertEqual(self.rows[key]["decision"], "UNCERTAIN")

    def test_decisive_fail_cancels_inflight_work(self):
        for policy in POLICIES:
            row = self.rows[("decisive_fail_cancel", policy)]
            self.assertEqual(row["decision"], "FAIL")
            self.assertEqual(row["decision_ready_ms"], 2)
            self.assertTrue(any(j["status"] == "CANCELLED_AFTER_FAIL" for j in row["jobs"]))

    def test_optional_deadline_does_not_block_mandatory_pass(self):
        row = self.rows[("optional_deadline", "PARALLEL_FANOUT")]
        self.assertEqual(row["decision"], "PASS")
        self.assertTrue(any(j["status"] == "DEADLINE" for j in row["jobs"] if not j["required"]))

    def test_resource_budgets_and_audit(self):
        self.assertEqual(audit(self.raw, WORKLOADS), [])
        for row in self.raw["cases"]:
            cap = 1 if row["policy"] == "SERIAL_VERIFIERS" else 3
            self.assertLessEqual(row["metrics"]["peak_concurrency"], cap)
            self.assertLessEqual(row["metrics"]["reserved_budget_units"], row["metrics"]["budget_limit_units"])

    def test_required_budget_failure_cancels_optional_work_immediately(self):
        case = {
            "case_id": "required_budget_miss_with_optional_inflight",
            "deadline_ms": 100,
            "budget_units": 3,
            "slowdown_per_other_worker": 0,
            "expected_decision": "UNCERTAIN",
            "jobs": [
                {"job_id": "a", "required": True, "dependencies": [], "duration_ms": 1,
                 "timeout_ms": None, "cost_units": 2, "outcome": "PASS", "input_sha256": "a"},
                {"job_id": "b", "required": True, "dependencies": ["a"], "duration_ms": 2,
                 "timeout_ms": None, "cost_units": 2, "outcome": "PASS", "input_sha256": "b"},
                {"job_id": "optional", "required": False, "dependencies": [], "duration_ms": 50,
                 "timeout_ms": None, "cost_units": 1, "outcome": "PASS", "input_sha256": "o"},
            ],
        }
        workload = {"schema": WORKLOADS["schema"], "config": WORKLOADS["config"], "cases": [case]}
        raw = run_all(workload)
        rows = raw["cases"]
        self.assertEqual(audit(raw, workload), [])
        parallel = next(row for row in rows if row["policy"] == "PARALLEL_FANOUT")
        optional = next(job for job in parallel["jobs"] if job["job_id"] == "optional")
        self.assertEqual(parallel["decision"], "UNCERTAIN")
        self.assertEqual(parallel["decision_ready_ms"], 1)
        self.assertEqual(optional["status"], "CANCELLED_AFTER_DECISION")
        self.assertEqual(optional["finish_ms"], 1)

    def test_corruption_controls(self):
        results = corruption_controls(self.raw, WORKLOADS)
        self.assertEqual(len(results), 6)
        self.assertTrue(all(x["rejected"] for x in results), results)


if __name__ == "__main__":
    unittest.main(verbosity=2)

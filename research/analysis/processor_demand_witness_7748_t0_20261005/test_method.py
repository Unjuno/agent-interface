import copy
import json
import pathlib
import unittest

import auditor
import candidate

ROOT = pathlib.Path(__file__).parent
FROZEN = json.loads((ROOT / "cases.json").read_text())
RAW = candidate.build(FROZEN)


class DemandWitnessTests(unittest.TestCase):
    def test_interval_oracle_matches_exhaustive_cases(self):
        result = auditor.audit(RAW, FROZEN)
        self.assertEqual(result, {"status": "PASS_METHOD_SCOPED", "errors": [], "cases": 6})
        rows = {r["input"]["id"]: r["result"] for r in RAW["rows"]}
        self.assertEqual(rows["feasible_poor_policy_miss"]["diagnosis"], "POLICY_MISS_ON_FEASIBLE_TRACE")
        self.assertTrue(rows["feasible_poor_policy_miss"]["all_exhaustive"]["feasible"])
        self.assertFalse(rows["control_feasible_joint_infeasible"]["all_demand"]["feasible"])
        self.assertTrue(rows["control_feasible_joint_infeasible"]["control_demand"]["feasible"])
        self.assertEqual(rows["nonpreemptive_unknown"]["status"], "UNKNOWN_MODEL_MISMATCH")
        self.assertEqual(rows["unknown_execution_hold"]["status"], "HOLD_NO_SCHEDULABILITY_INPUTS")

    def test_boundary_equality_is_not_a_demand_witness(self):
        result = next(r["result"] for r in RAW["rows"] if r["input"]["id"] == "exact_boundary_feasible")
        self.assertTrue(result["all_demand"]["feasible"])
        self.assertEqual(result["all_demand"]["max_excess"], 0)
        self.assertTrue(result["all_exhaustive"]["feasible"])

    def test_independent_audit_rejects_frozen_input_and_result_mutations(self):
        mutations = (
            lambda r: r["rows"][0]["input"]["jobs"][0].update(release=1),
            lambda r: r["rows"][0]["input"]["jobs"][0].update(execution=2),
            lambda r: r["rows"][0]["input"]["jobs"][0].update(deadline=3),
            lambda r: r["rows"][0]["result"].update(diagnosis="JOINT_DEMAND_INFEASIBLE"),
            lambda r: r["rows"][0]["result"]["all_demand"]["witnesses"].append(
                {"start":0,"end":1,"demand":0,"capacity":1,"excess":0}),
            lambda r: r["rows"][0]["result"]["bad_policy"]["schedule"][0].update(job="c0"),
        )
        for mutate in mutations:
            changed = copy.deepcopy(RAW)
            mutate(changed)
            with self.subTest(mutation=mutate.__code__.co_firstlineno):
                self.assertEqual(auditor.audit(changed, FROZEN)["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()

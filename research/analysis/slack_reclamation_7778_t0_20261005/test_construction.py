import unittest
import json

from candidate import can_steal, classify, run_policy
from generator import workloads
from auditor import max_optional_service, validate_row


def json_clone(value):
    return json.loads(json.dumps(value))


class ConstructionTests(unittest.TestCase):
    def test_fixture_grid_is_unique_and_bounded(self):
        cases = workloads()
        self.assertEqual(len(cases), 9)
        self.assertEqual(len({x["trace_id"] for x in cases}), len(cases))
        for case in cases:
            self.assertEqual(len({j["id"] for j in case["jobs"]}), len(case["jobs"]))
            self.assertLessEqual(len([j for j in case["jobs"] if j["class"] == "control"]), 3)

    def test_incomplete_future_contract_never_authorizes_stealing(self):
        contract = {"preemptive": True, "min_interarrival": 1,
                    "max_execution": 2, "relative_deadline": 1}
        self.assertFalse(can_steal(0, contract, 8, None, 0))

    def test_declared_unknown_and_invalid_cases_fail_closed(self):
        by_name = {x["trace_id"]: x for x in workloads()}
        self.assertEqual(classify(by_name["unknown_wcet"]), "HOLD_MODEL_MISMATCH")
        self.assertEqual(classify(by_name["unknown_nonpreemptive"]), "HOLD_MODEL_MISMATCH")
        self.assertEqual(classify(by_name["invalid_job_class"]), "HOLD_INVALID_JOB_CLASS")

    def test_valid_slack_trace_preserves_control_deadlines(self):
        by_name = {x["trace_id"]: x for x in workloads()}
        row = run_policy(by_name["idle_gaps"], "DEMAND_GUARDED_SLACK_STEAL")
        self.assertEqual(row["status"], "COMPLETE")
        self.assertTrue(row["control_completed"])
        self.assertLessEqual(row["soft_service"],
                             max_optional_service(by_name["idle_gaps"]["jobs"], 24))

    def test_raw_mutations_are_rejected(self):
        trace = next(x for x in workloads() if x["trace_id"] == "idle_gaps")
        original = run_policy(trace, "STATIC_RESERVATION")
        mutations = []
        x = json_clone(original); x["events"] = x["events"][:-1]; mutations.append(x)
        x = json_clone(original); x["events"][1]["tick"] = 0; mutations.append(x)
        x = json_clone(original); x["events"][1]["arrivals"] = []; mutations.append(x)
        x = json_clone(original); x["events"][0]["action"] = ["s0", "s1"]; mutations.append(x)
        x = json_clone(original); x["events"][1]["reserved"] = True; mutations.append(x)
        x = json_clone(original); x["events"][0]["action"] = "c0"; mutations.append(x)
        self.assertTrue(all(not validate_row(trace, x)[0] for x in mutations))


if __name__ == "__main__":
    unittest.main()

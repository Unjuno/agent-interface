import copy
import json
import unittest
from pathlib import Path

from audit import audit
from candidate import run

CONSTRUCTION = {
    "schema": "service-fairness-public-v1",
    "allocation": "LONG-HORIZON-SERVICE-DEBT-6613-T0-HOSTCPU-20261002-01",
    "policies": ["fifo", "fastest", "batch2", "service_debt"],
    "batch_window": 2,
    "max_time": 24,
    "cases": [
        {"id":"balanced_equal_load","requests":[
            {"id":"eq_a0","principal":"A","arrival":0,"service":1,"deadline":10,"authority":True,"joint_grant":True,"conflict_free":True},
            {"id":"eq_b0","principal":"B","arrival":0,"service":1,"deadline":10,"authority":True,"joint_grant":True,"conflict_free":True},
            {"id":"eq_c0","principal":"C","arrival":0,"service":1,"deadline":10,"authority":True,"joint_grant":True,"conflict_free":True}],"revocations":[],"safety_release_times":[]},
        {"id":"asymmetric_repeated_contention","requests":[
            *[{"id":f"as_a{i}","principal":"A","arrival":0,"service":1,"deadline":18,"authority":True,"joint_grant":True,"conflict_free":True} for i in range(4)],
            *[{"id":f"as_b{i}","principal":"B","arrival":0,"service":1,"deadline":18,"authority":True,"joint_grant":True,"conflict_free":True} for i in range(2)],
            *[{"id":f"as_c{i}","principal":"C","arrival":0,"service":1,"deadline":18,"authority":True,"joint_grant":True,"conflict_free":True} for i in range(2)]],"revocations":[],"safety_release_times":[]},
        {"id":"bursty_variable_service","requests":[
            {"id":"burst_a10","principal":"A","arrival":0,"service":2,"deadline":16,"authority":True,"joint_grant":True,"conflict_free":True},
            {"id":"burst_b10","principal":"B","arrival":0,"service":1,"deadline":16,"authority":True,"joint_grant":True,"conflict_free":True},
            {"id":"burst_c10","principal":"C","arrival":1,"service":2,"deadline":18,"authority":True,"joint_grant":True,"conflict_free":True},
            {"id":"burst_b11","principal":"B","arrival":2,"service":1,"deadline":18,"authority":True,"joint_grant":True,"conflict_free":True}],"revocations":[],"safety_release_times":[]},
        {"id":"eligibility_and_release_controls","requests":[
            {"id":"ctrl_a20","principal":"A","arrival":0,"service":1,"deadline":10,"authority":True,"joint_grant":True,"conflict_free":True},
            {"id":"ctrl_b20","principal":"B","arrival":0,"service":1,"deadline":10,"authority":True,"joint_grant":True,"conflict_free":True,"revoked_at":1},
            {"id":"ctrl_c20","principal":"C","arrival":0,"service":1,"deadline":10,"authority":True,"joint_grant":False,"conflict_free":True},
            {"id":"ctrl_d20","principal":"D","arrival":0,"service":1,"deadline":10,"authority":False,"joint_grant":True,"conflict_free":True},
            {"id":"ctrl_e20","principal":"E","arrival":0,"service":1,"deadline":10,"authority":True,"joint_grant":True,"conflict_free":False}],"revocations":[{"principal":"B","at":1}],"safety_release_times":[0]},
        {"id":"all_ineligible","requests":[
            {"id":"deny_b30","principal":"B","arrival":0,"service":1,"deadline":8,"authority":False,"joint_grant":True,"conflict_free":True},
            {"id":"deny_c30","principal":"C","arrival":0,"service":1,"deadline":8,"authority":True,"joint_grant":False,"conflict_free":True},
            {"id":"deny_d30","principal":"D","arrival":0,"service":1,"deadline":8,"authority":True,"joint_grant":True,"conflict_free":False}],"revocations":[],"safety_release_times":[]}
    ]
}
CONSTRUCTION_ORACLE = {
    "eligible_request_ids": ["eq_a0","eq_b0","eq_c0","as_a0","as_a1","as_a2","as_a3",
                             "as_b0","as_b1","as_c0","as_c1","burst_a10","burst_b10",
                             "burst_c10","burst_b11","ctrl_a20","ctrl_b20"],
    "exact_effect_success": {"eq_a0":True,"eq_b0":True,"eq_c0":True,"as_a0":True,"as_a1":True,
                             "as_a2":True,"as_a3":True,"as_b0":True,"as_b1":True,"as_c0":True,"as_c1":True,
                             "burst_a10":True,"burst_b10":True,"burst_c10":True,"burst_b11":False,
                             "ctrl_a20":True,"ctrl_b20":True}
}


class ServiceFairnessMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = run(CONSTRUCTION)
        cls.result = audit(CONSTRUCTION, CONSTRUCTION_ORACLE, cls.raw)

    def test_policy_trace_coverage_and_independent_reference(self):
        self.assertEqual(len(self.raw["rows"]), 20)
        self.assertEqual(self.result["status"], "METHOD_PASS_SCOPED", self.result["errors"])
        self.assertEqual(self.result["errors"], [])

    def test_service_debt_strictly_reduces_asymmetric_bypass_streak(self):
        rows = {row["policy"]: row for row in self.result["independently_reconstructed"]
                if row["case_id"] == "asymmetric_repeated_contention"}
        self.assertLess(rows["service_debt"]["max_consecutive_bypasses"], rows["fifo"]["max_consecutive_bypasses"])
        self.assertLess(rows["service_debt"]["max_consecutive_bypasses"], rows["fastest"]["max_consecutive_bypasses"])
        self.assertLess(rows["service_debt"]["max_consecutive_bypasses"], rows["batch2"]["max_consecutive_bypasses"])

    def test_missing_grant_conflict_revocation_and_safety_release(self):
        for row in (x for x in self.raw["rows"] if x["case_id"] == "eligibility_and_release_controls"):
            attempts = {event["request"] for event in row["events"] if event["kind"] == "DISPATCH"}
            self.assertTrue(attempts <= {"ctrl_a20"})
            self.assertEqual(row["events"][0], {"kind": "SAFETY_RELEASE", "time": 0})

    def test_denied_requests_are_not_a_starvation_cohort(self):
        for row in (x for x in self.raw["rows"] if x["case_id"] == "all_ineligible"):
            self.assertEqual(row["attempted"], 0)
            self.assertEqual(row["max_consecutive_bypasses"], 0)
            self.assertEqual(row["starvation_episodes"], 0)

    def test_audit_rejects_four_declared_corruptions(self):
        corruptions = []

        x = copy.deepcopy(self.raw)
        denied = next(r for r in x["rows"] if r["case_id"] == "all_ineligible")
        denied["starvation_episodes"] = 1
        corruptions.append(x)  # count denied work as starvation

        x = copy.deepcopy(self.raw)
        attempted = next(r for r in x["rows"] if r["case_id"] == "bursty_variable_service")
        event = next(e for e in attempted["events"] if e["kind"] == "DISPATCH")
        event["verified"] = True
        corruptions.append(x)  # turn an attempt into an oracle-verified effect

        x = copy.deepcopy(self.raw)
        denied = next(r for r in x["rows"] if r["case_id"] == "eligibility_and_release_controls")
        dispatch = next(e for e in denied["events"] if e["kind"] == "DISPATCH")
        dispatch["request"] = "c20"  # use fairness debt to bypass a missing joint grant
        corruptions.append(x)

        x = copy.deepcopy(self.raw)
        safety = next(r for r in x["rows"] if r["case_id"] == "eligibility_and_release_controls")
        safety["events"] = [e for e in safety["events"] if e["kind"] != "SAFETY_RELEASE"]
        corruptions.append(x)  # suppress the independent mandatory release

        self.assertEqual(len(corruptions), 4)
        for malformed in corruptions:
            with self.subTest(corruption=len(malformed["rows"])):
                self.assertEqual(audit(CONSTRUCTION, CONSTRUCTION_ORACLE, malformed)["status"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)

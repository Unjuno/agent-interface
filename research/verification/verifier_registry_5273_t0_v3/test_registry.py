import copy
import json
import unittest
from pathlib import Path

from audit import audit_rows, independent_ir_valid, raw_field_set_valid
from candidate import preflight
from fixtures import CASES, RESOURCES
from oracle import EXPECTED_ROWS, expected_plan

HERE=Path(__file__).resolve().parent
REGISTRY=json.loads((HERE/"registry.json").read_text())


def run_plans(cases=CASES):
    return [{"case_id":case["case_id"],**preflight(case["case_id"],case["ir"],case["assignments"],REGISTRY,RESOURCES)} for case in cases]


class FullPlanRegistryV3Tests(unittest.TestCase):
    def test_all_plan_rows_and_aggregate_match_oracle(self):
        plans=run_plans()
        self.assertTrue(audit_rows(CASES,plans)["ok"])
        for case,plan in zip(CASES,plans):
            ids=[row["check_id"] for row in case["ir"]["checks"]]
            expected_status,expected_reasons=expected_plan(ids)
            self.assertEqual((plan["status"],plan["reasons"]),(expected_status,expected_reasons))
            for decision in plan["decisions"]:
                status,reasons,cost=EXPECTED_ROWS[decision["check_id"]]
                self.assertEqual((decision["status"],tuple(decision["reasons"]),decision["estimated_cost_ms"]),(status,reasons,cost))

    def test_full_mandatory_set_cannot_be_hidden_by_selected_assignment(self):
        case=CASES[-1]
        self.assertEqual([row["status"] for row in run_plans()[-1]["decisions"]],["UNAVAILABLE","COMPATIBLE"])
        self.assertEqual(preflight(case["case_id"],case["ir"],case["assignments"],REGISTRY,RESOURCES)["status"],"UNAVAILABLE")

    def test_duplicate_missing_and_extra_raw_check_ids_fail(self):
        plans=run_plans()
        mutated=copy.deepcopy(plans)
        mutated[0]["decisions"].append(copy.deepcopy(mutated[0]["decisions"][0]))
        self.assertFalse(audit_rows(CASES,mutated)["ok"])
        mutated=copy.deepcopy(plans)
        mutated[-1]["decisions"].pop()
        self.assertFalse(audit_rows(CASES,mutated)["ok"])
        mutated=copy.deepcopy(plans)
        mutated[-1]["decisions"].append(dict(mutated[-1]["decisions"][-1],check_id="extra"))
        self.assertFalse(audit_rows(CASES,mutated)["ok"])

    def test_exact_raw_and_decision_field_sets_are_enforced(self):
        plans=run_plans()
        extra=copy.deepcopy(plans)
        extra[0]["decisions"][0]["unreviewed_field"]=True
        self.assertFalse(audit_rows(CASES,extra)["ok"])
        self.assertFalse(independent_ir_valid(dict(CASES[0]["ir"],unexpected=True)))
        self.assertFalse(raw_field_set_valid({"schema":"verifier_registry_5273_raw.v3","plans":[],"unexpected":True}))

    def test_assignment_bijection_and_output_role_are_required(self):
        case=copy.deepcopy(CASES[-1])
        with self.assertRaisesRegex(ValueError,"every IR check"):
            preflight(case["case_id"],case["ir"],case["assignments"][:1],REGISTRY,RESOURCES)
        case=copy.deepcopy(CASES[5])
        case["assignments"][0]["output_evidence_role"]="NOT_AN_IR_ROLE"
        with self.assertRaisesRegex(ValueError,"output role"):
            preflight(case["case_id"],case["ir"],case["assignments"],REGISTRY,RESOURCES)


if __name__=="__main__": unittest.main()

import copy
import unittest

from spec_fixture import SPEC
from candidate import evaluate
from auditor import audit


class DegradationPolicyComparisonTests(unittest.TestCase):
    def test_three_required_arms_reconstruct_and_find_common_cause_overclaims(self):
        candidate = evaluate(SPEC)
        result = audit(SPEC, candidate)
        self.assertEqual(result["audit_integrity"], "PASS", result)
        self.assertEqual(result["cases_reconstructed"], 10)
        self.assertEqual(result["independence_overclaim_cases"], 4)
        self.assertEqual(result["independence_overclaim_operations"], 6)
        self.assertEqual(result["dependency_aware_unsupported_operations"], 0)
        self.assertEqual(result["unknown_fail_closed_cases"], 1)
        self.assertEqual(result["unknown_fail_closed_admitted_operations"], 0)
        self.assertEqual(result["mandatory_release_obligations_verified"], 10)
        self.assertEqual(result["dispatches"], 0)

    def test_dependency_aware_policy_preserves_only_supported_partial_outcomes(self):
        candidate = evaluate(SPEC)
        rows = {row["case_id"]: row for row in candidate["cases"]}
        self.assertEqual(
            [item["operation"] for item in rows["common_semantic_scheduler_stall"]["arms"]["dependency_aware_contract"]],
            ["inspect_raw"],
        )
        self.assertEqual(
            [item["operation"] for item in rows["common_parser_lineage_corruption"]["arms"]["dependency_aware_contract"]],
            ["inspect_raw"],
        )
        self.assertEqual(rows["common_semantic_scheduler_stall"]["arms"]["independence_assuming_lookup"][-1]["operation"], "show_effect_receipt")
        self.assertEqual(rows["unknown_semantic_dependency"]["arms"]["unknown_dependency_fail_closed"], [])

    def test_auditor_rejects_six_semantic_corruptions(self):
        original = evaluate(SPEC)
        mutations = []
        item = copy.deepcopy(original); item["cases"][3]["arms"]["independence_assuming_lookup"].pop(); mutations.append(item)
        item = copy.deepcopy(original); item["cases"][9]["arms"]["unknown_dependency_fail_closed"].append({"operation":"present_semantics","source":"semantic_observation","claim":"SEMANTIC_VERIFIED","freshness":"CURRENT"}); mutations.append(item)
        item = copy.deepcopy(original); item["cases"][0]["arms"]["dependency_aware_contract"][0]["claim"]="EFFECT_VERIFIED"; mutations.append(item)
        item = copy.deepcopy(original); item["cases"][0]["arms"]["dependency_aware_contract"].append({"operation":"dispatch_action","source":"planner","claim":"ACTION_AUTHORIZED","freshness":"CURRENT"}); mutations.append(item)
        item = copy.deepcopy(original); item["cases"][9]["release_obligation"]="NONE"; mutations.append(item)
        altered_spec=copy.deepcopy(SPEC); altered_spec["components"]["verifier"].remove("shared_parser"); mutations.append((altered_spec,original))
        self.assertEqual(len(mutations),6)
        for item in mutations:
            raw_spec, raw_candidate = item if isinstance(item,tuple) else (SPEC,item)
            self.assertEqual(audit(raw_spec,raw_candidate)["audit_integrity"],"FAIL")


if __name__ == "__main__":
    unittest.main(verbosity=2)

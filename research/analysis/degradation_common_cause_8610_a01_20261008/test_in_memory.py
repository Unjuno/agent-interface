import copy
import json
from pathlib import Path
import sys
import unittest

package = Path("research/analysis/degradation_common_cause_8610_a01_20261008")
sys.path.insert(0, str(package.resolve()))
import candidate
import auditor

SPEC = json.loads((package / "spec.json").read_text(encoding="utf-8"))
RESULT = candidate.evaluate(SPEC)

class InMemoryContractTests(unittest.TestCase):
    def test_independent_audit_reconstructs_incremental_safe_outcomes(self):
        result = auditor.audit(SPEC, RESULT)
        self.assertEqual(result["audit_integrity"], "PASS", result)
        self.assertEqual(result["cases_reconstructed"], 9)
        self.assertEqual(result["additional_supported_outcomes"], 11)
        self.assertEqual(result["unsafe_control_rejections"], 3)
        self.assertEqual(result["authority_inflation"], 0)
        self.assertEqual(result["false_effect_claims"], 0)
        self.assertEqual(result["release_obligations_verified"], 9)
        self.assertEqual(result["dispatches"], 0)

    def test_shared_scheduler_loss_preserves_raw_only_inspection(self):
        cases = {row["case_id"]: row for row in RESULT["cases"]}
        self.assertEqual(cases["common_semantic_scheduler_stall"]["binary"], [])
        self.assertEqual([row["operation"] for row in cases["common_semantic_scheduler_stall"]["contract"]], ["inspect_raw"])

    def test_six_semantic_mutations_fail_independent_audit(self):
        mutations = []
        item = copy.deepcopy(RESULT); item["cases"][1]["contract"].pop(); mutations.append(item)
        item = copy.deepcopy(RESULT); item["cases"][6]["contract"].append({"operation":"present_semantics","source":"semantic_observation","claim":"SEMANTIC_VERIFIED","freshness":"CURRENT"}); mutations.append(item)
        item = copy.deepcopy(RESULT); item["cases"][0]["contract"][0]["claim"]="EFFECT_VERIFIED"; mutations.append(item)
        item = copy.deepcopy(RESULT); item["cases"][0]["contract"][1]["source"]="raw_observation"; mutations.append(item)
        item = copy.deepcopy(RESULT); item["cases"][0]["contract"].append({"operation":"dispatch_action","source":"planner","claim":"ACTION_AUTHORIZED","freshness":"CURRENT"}); mutations.append(item)
        item = copy.deepcopy(RESULT); item["cases"][7]["release_obligation"]="NONE"; mutations.append(item)
        self.assertEqual(len(mutations), 6)
        self.assertTrue(all(auditor.audit(SPEC, item)["audit_integrity"] == "FAIL" for item in mutations))

if __name__ == "__main__":
    unittest.main(verbosity=2)
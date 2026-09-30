import copy
import json
import unittest
from pathlib import Path

from candidate import preflight
from oracle import EXPECTED, audit

HERE = Path(__file__).resolve().parent


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((HERE / "registry.json").read_text())
        cls.cases = json.loads((HERE / "cases.json").read_text())

    def test_frozen_cases_match_literal_oracle(self):
        decisions = []
        for item in self.cases["cases"]:
            result = preflight({"schema": "verifier_plan.v0.1", "checks": [item["check"]]}, self.registry, self.cases["resources"])
            decisions.extend(result["decisions"])
        raw = {"decisions": decisions}
        self.assertEqual(audit(self.cases, raw)["disposition"], "PASS_HOST_CONSTRUCTION_ONLY")

    def test_duplicate_registry_id_rejected(self):
        reg = copy.deepcopy(self.registry)
        reg["descriptors"].append(copy.deepcopy(reg["descriptors"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate verifier"):
            preflight({"schema": "verifier_plan.v0.1", "checks": []}, reg, self.cases["resources"])

    def test_registry_authority_escalation_rejected(self):
        reg = copy.deepcopy(self.registry)
        reg["authority"] = "execute"
        with self.assertRaisesRegex(ValueError, "authority"):
            preflight({"schema": "verifier_plan.v0.1", "checks": []}, reg, self.cases["resources"])

    def test_missing_resource_is_unavailable_not_compatible(self):
        item = next(x for x in self.cases["cases"] if x["case_id"] == "resource_unavailable")
        result = preflight({"schema": "verifier_plan.v0.1", "checks": [item["check"]]}, self.registry, self.cases["resources"])
        self.assertEqual(result["decisions"][0]["status"], "UNAVAILABLE")
        self.assertEqual(result["decisions"][0]["dispatch_count"], 0)

    def test_auditor_rejects_changed_expected_label(self):
        decisions=[]
        for item in self.cases["cases"]:
            decisions += preflight({"schema":"verifier_plan.v0.1","checks":[item["check"]]},self.registry,self.cases["resources"])["decisions"]
        corrupted=copy.deepcopy(self.cases)
        corrupted["cases"][0]["expected"]="REJECTED"
        self.assertEqual(audit(corrupted,{"decisions":decisions})["disposition"],"FAIL")


if __name__ == "__main__":
    unittest.main()

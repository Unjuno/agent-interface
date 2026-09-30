import copy
import json
import unittest
from pathlib import Path

from candidate import preflight
from oracle import EXPECTED

HERE = Path(__file__).resolve().parent


class RegistryV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((HERE / "registry.json").read_text())
        cls.cases = json.loads((HERE / "cases.json").read_text())

    def test_all_actual_ir_cases_match_test_oracle(self):
        self.assertEqual({row["case_id"] for row in self.cases["cases"]}, set(EXPECTED))
        for row in self.cases["cases"]:
            got = preflight(row["ir"], row["assignment"], self.registry, self.cases["resources"])
            self.assertEqual((got["status"], tuple(got["reasons"])), EXPECTED[row["case_id"]], row["case_id"])
            self.assertEqual((got["dispatch_count"], got["authority"], got["cost_basis"]), (0, "none", "declared_estimate_not_measurement"))

    def test_descriptor_authority_escalation_rejected(self):
        reg = copy.deepcopy(self.registry)
        reg["descriptors"][0]["authority"] = "execute"
        row = self.cases["cases"][0]
        with self.assertRaisesRegex(ValueError, "authority"):
            preflight(row["ir"], row["assignment"], reg, self.cases["resources"])

    def test_mixed_stale_unavailable_is_hard_rejection(self):
        row = next(x for x in self.cases["cases"] if x["case_id"] == "hard_incompatibility_precedes_unavailable")
        got = preflight(row["ir"], row["assignment"], self.registry, self.cases["resources"])
        self.assertEqual(got["status"], "REJECTED")

    def test_duplicate_raw_ids_and_missing_rows_fail_auditor(self):
        from audit import audit_rows
        for rows in ([{"check_id":"x"}, {"check_id":"x"}], [{"check_id":"c1"}],
                     [{"check_id":f"c{i}"} for i in range(1,11)] + [{"check_id":"extra"}]):
            self.assertEqual(audit_rows(self.cases, {"decisions":rows})["disposition"], "FAIL_ROW_IDENTITY")

    def test_wrong_output_role_is_rejected(self):
        row = next(x for x in self.cases["cases"] if x["case_id"] == "wrong_output_role")
        self.assertIn("wrong_output_role", preflight(row["ir"], row["assignment"], self.registry, self.cases["resources"])["reasons"])

    def test_resource_snapshot_types_are_strict(self):
        row = self.cases["cases"][0]
        with self.assertRaisesRegex(ValueError, "resource snapshot"):
            preflight(row["ir"], row["assignment"], self.registry, {"cpu": 1})

    def test_non_boolean_side_effect_policy_is_rejected(self):
        row = self.cases["cases"][0]
        assignment = dict(row["assignment"], side_effects_allowed="false")
        with self.assertRaisesRegex(ValueError, "assignment field types"):
            preflight(row["ir"], assignment, self.registry, self.cases["resources"])

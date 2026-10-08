"""Construction tests for the #5269 mandatory-coverage boundary."""
import copy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "verification_ir_5268_v1"
sys.path.insert(0, str(PARENT))

from candidate import PRIMITIVES, lower_action  # noqa: E402
from coverage import validate_coverage  # noqa: E402


def fixtures():
    formal = json.loads((PARENT / "FORMAL-01.json").read_text())
    oracle = json.loads((PARENT / "oracle_expected.json").read_text())
    cases = {row["case_id"]: row for row in formal["cases"]}
    return cases, oracle


class MandatoryCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.oracle = fixtures()

    def plan(self, case_id):
        case = self.cases[case_id]
        return lower_action(case["action"])

    def requirements(self, case_id):
        return self.plan(case_id)

    def assert_rejected(self, case_id, mutate, profiles=None):
        plan = copy.deepcopy(self.plan(case_id))
        mutate(plan)
        with self.assertRaises(ValueError):
            validate_coverage(self.requirements(case_id), plan, profiles or {})

    def test_complete_frozen_plans_are_accepted_without_truth_or_authority(self):
        for case_id in sorted(self.cases):
            with self.subTest(case=case_id):
                result = validate_coverage(self.requirements(case_id), self.plan(case_id), {})
                self.assertEqual(result["status"], "PLAN_COMPLETE")
                self.assertNotIn("authority", result)
                self.assertNotIn("current", result)
                self.assertNotIn("effect_truth", result)
                self.assertNotIn("verdict", result)

    def test_required_policy_rows_match_the_parent_literal_oracle(self):
        fields = ("check_id", "primitive", "subject_ref", "criticality",
                  "required_evidence_role", "verifier_class", "dependencies")
        for case_id in sorted(self.cases):
            with self.subTest(case=case_id):
                actual = [tuple(row[key] for key in fields)
                          for row in self.requirements(case_id)["checks"]]
                self.assertEqual(actual, [tuple(row) for row in self.oracle[case_id]])

    def test_each_mandatory_check_omission_is_rejected(self):
        for case_id in sorted(self.cases):
            for required in self.requirements(case_id)["checks"]:
                if required["criticality"] == "OPTIONAL":
                    continue
                with self.subTest(case=case_id, check=required["check_id"]):
                    self.assert_rejected(case_id, lambda plan, cid=required["check_id"]:
                                         plan["checks"].__setitem__(
                                             slice(None), [c for c in plan["checks"]
                                                           if c["check_id"] != cid]))

    def test_downgrade_wrong_subject_role_and_intent_generation_are_rejected(self):
        self.assert_rejected("iid-baseline", lambda p: p["checks"][0].update(criticality="OPTIONAL"))
        self.assert_rejected("iid-baseline", lambda p: p["checks"][0].update(subject_ref="window:other"))
        self.assert_rejected("iid-baseline", lambda p: p["checks"][0].update(
            required_evidence_role="CURRENT_INTENT"))
        self.assert_rejected("iid-baseline", lambda p: p["checks"][1].update(
            subject_ref="intent:save-v2"))

    def test_deadline_infeasible_verifier_is_rejected_from_frozen_profile(self):
        plan = self.plan("iid-baseline")
        optional = copy.deepcopy(plan["checks"][0])
        optional.update(check_id="optional.deadline.probe", primitive="META.COVERAGE",
                        subject_ref="a-01", criticality="OPTIONAL",
                        required_evidence_role="COVERAGE_REPORT",
                        verifier_class="bounded_probe", dependencies=[], deadline=10)
        plan["checks"].append(optional)
        profiles = {"bounded_probe": {"upper_bound_ms": 11}}
        with self.assertRaisesRegex(ValueError, "deadline"):
            validate_coverage(self.requirements("iid-baseline"), plan, profiles)

    def test_unknown_primitive_and_duplicate_semantic_check_are_rejected(self):
        self.assert_rejected("iid-baseline", lambda p: p["checks"][0].update(
            primitive="TARGET.NOVEL"))
        def duplicate(plan):
            extra = copy.deepcopy(plan["checks"][0])
            extra["check_id"] = "target.current.copy"
            extra["dependencies"] = []
            plan["checks"].append(extra)
        self.assert_rejected("iid-baseline", duplicate)

    def test_external_side_effect_case_rejects_missing_effect_safeguards(self):
        def remove_effects(plan):
            plan["checks"][:] = [c for c in plan["checks"]
                                 if not c["primitive"].startswith("EFFECT.")]
        self.assert_rejected("external-side-effect", remove_effects)

    def test_optional_diagnostic_can_be_omitted_or_added_without_changing_policy(self):
        plan = self.plan("optional-diagnostic")
        plan["checks"][:] = [c for c in plan["checks"] if c["criticality"] != "OPTIONAL"]
        self.assertEqual(validate_coverage(self.requirements("optional-diagnostic"), plan, {})[
                         "status"], "PLAN_COMPLETE")
        added = self.plan("iid-baseline")
        added["checks"].append({
            **copy.deepcopy(added["checks"][0]), "check_id": "meta.coverage",
            "primitive": "META.COVERAGE", "subject_ref": "a-01",
            "criticality": "OPTIONAL", "required_evidence_role": "COVERAGE_REPORT",
            "verifier_class": "coverage_report", "dependencies": [],
        })
        self.assertEqual(validate_coverage(self.requirements("iid-baseline"), added, {})[
                         "status"], "PLAN_COMPLETE")

    def test_frozen_ontology_has_no_risk_escalation_primitive(self):
        self.assertFalse(any("ESCALAT" in primitive for primitive in PRIMITIVES))


if __name__ == "__main__":
    unittest.main()

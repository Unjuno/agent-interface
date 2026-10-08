import unittest

from candidate import plan_recovery
from run_candidate import evaluate


def branch_local_revision_case():
    return {
        "case_id": "branch_local_revision",
        "provenance_complete": True,
        "current_versions": {
            "left_source": 1,
            "right_source": 1,
            "left_cfg": 2,
            "right_cfg": 1,
            "right_draft": 1,
        },
        "nodes": [
            {"id": "observe_left", "kind": "observe", "deps": [], "reads": {"left_source": 1}},
            {"id": "observe_right", "kind": "observe", "deps": [], "reads": {"right_source": 1}},
            {"id": "derive_left", "kind": "compute", "deps": ["observe_left"], "reads": {"left_cfg": 1}},
            {"id": "derive_right", "kind": "compute", "deps": ["observe_right"], "reads": {"right_cfg": 1}},
            {"id": "prepare_right", "kind": "prepare", "deps": ["derive_right"], "reads": {"right_draft": 1}},
            {"id": "send_effect", "kind": "effect", "deps": ["derive_left"], "receipt": "verified_effect"},
            {"id": "verify_terminal", "kind": "verify", "deps": ["send_effect"], "receipt": "verified_terminal"},
        ],
    }


class RecoveryPlanTests(unittest.TestCase):
    def test_runner_preserves_each_authored_revision_schedule(self):
        payload = {
            "base_nodes": [{"id": "c", "kind": "compute", "deps": [], "reads": {"x": 1}}],
            "cases": [
                {"case_id": "x1", "provenance_complete": True, "current_versions": {"x": 1}},
                {"case_id": "x2", "provenance_complete": True, "current_versions": {"x": 2}},
            ],
        }

        result = evaluate(payload)

        self.assertEqual([row["case_id"] for row in result["results"]], ["x1", "x2"])
        self.assertEqual(result["results"][1]["plan"]["recompute"]["SELECTIVE_VALIDITY_RECOVERY"], ["c"])

    def test_selective_reuses_valid_independent_work_after_first_conflict(self):
        plan = plan_recovery(branch_local_revision_case())

        self.assertEqual(
            plan["recompute"],
            {
                "FULL_RESTART": ["observe_left", "observe_right", "derive_left", "derive_right", "prepare_right"],
                "EARLIEST_CONFLICT_SUFFIX": ["derive_left", "derive_right", "prepare_right"],
                "SELECTIVE_VALIDITY_RECOVERY": ["derive_left"],
            },
        )
        self.assertEqual(plan["historical_verifications"], ["verify_terminal"])

    def test_recovery_never_resubmits_effects_even_when_receipt_is_ambiguous(self):
        case = branch_local_revision_case()
        next(node for node in case["nodes"] if node["id"] == "send_effect")["receipt"] = "ambiguous_delivery"
        next(node for node in case["nodes"] if node["id"] == "verify_terminal")["receipt"] = "unknown"

        plan = plan_recovery(case)

        self.assertEqual(plan["dispatch_effects"], [])
        self.assertEqual(plan["reconcile_effects"], ["send_effect"])
        self.assertEqual(plan["preserved_effects"], [])
        self.assertEqual(plan["historical_verifications"], [])

    def test_verified_no_effect_does_not_itself_authorize_an_effect_dispatch(self):
        case = branch_local_revision_case()
        next(node for node in case["nodes"] if node["id"] == "send_effect")["receipt"] = "verified_no_effect"

        plan = plan_recovery(case)

        self.assertEqual(plan["disposition"], "PASS_PLAN")
        self.assertEqual(plan["dispatch_effects"], [])
        self.assertEqual(plan["reconcile_effects"], [])

    def test_duplicate_node_identity_rejects_the_entire_plan(self):
        case = branch_local_revision_case()
        case["nodes"][1]["id"] = "observe_left"

        plan = plan_recovery(case)

        self.assertEqual(plan["disposition"], "INVALID_PLAN")
        self.assertEqual(plan["dispatch_effects"], [])

    def test_incomplete_provenance_fails_closed_and_does_not_increase_reuse(self):
        complete = plan_recovery(branch_local_revision_case())
        incomplete_case = branch_local_revision_case()
        incomplete_case["provenance_complete"] = False
        incomplete = plan_recovery(incomplete_case)

        self.assertEqual(incomplete["disposition"], "HOLD_INCOMPLETE_PROVENANCE")
        self.assertLessEqual(
            len(incomplete["reused"]["SELECTIVE_VALIDITY_RECOVERY"]),
            len(complete["reused"]["SELECTIVE_VALIDITY_RECOVERY"]),
        )
        self.assertEqual(incomplete["dispatch_effects"], [])


if __name__ == "__main__":
    unittest.main()

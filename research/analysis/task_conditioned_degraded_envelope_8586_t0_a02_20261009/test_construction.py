from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import auditor
import candidate


HERE = Path(__file__).parent
MODEL = json.loads((HERE / "model.json").read_text(encoding="utf-8"))
RAW = {"schema": "TDCE_A02_CANDIDATE_RAW_V1", "rows": candidate.build_rows(MODEL)}


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.raw = copy.deepcopy(RAW)

    def test_full_task_local_grid_matches_independent_oracle(self):
        result = auditor.audit(MODEL, self.raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED", result["errors"])
        self.assertEqual(result["expected_rows"], 336)
        self.assertEqual(result["counts"]["distinct_two_capability_joint_false_continuations"], 2)

    def test_capability_universes_have_three_or_four_members(self):
        self.assertTrue(all(3 <= len(t["capabilities"]) <= 4 for t in MODEL["tasks"]))

    def test_both_distinct_joint_witnesses_are_present(self):
        for task_id, lost, context in auditor.WITNESSES:
            row = next(r for r in self.raw["rows"] if (r["task_id"], tuple(r["lost_capabilities"]), r["context"]) == (task_id, lost, context))
            self.assertEqual(row["edgewise_decision"], "CONTINUE")
            self.assertEqual(row["tdce_decision"], "STOP_UNKNOWN")

    def test_single_loss_sibling_preserving_routes_remain_qualified(self):
        for lost in (["semantic_target"], ["native_effect_check"]):
            row = next(r for r in self.raw["rows"] if r["task_id"] == "preserve_sibling_edit" and r["lost_capabilities"] == lost and r["context"] == "valid")
            self.assertEqual(row["tdce_decision"], "CONTINUE_WITH_LIMITS")

    def test_single_loss_window_routes_remain_qualified(self):
        for lost in (["window_identity"], ["focus_stability"]):
            row = next(r for r in self.raw["rows"] if r["task_id"] == "focused_window_action" and r["lost_capabilities"] == lost and r["context"] == "valid")
            self.assertEqual(row["tdce_decision"], "CONTINUE_WITH_LIMITS")

    def test_missing_row_is_rejected(self):
        self.raw["rows"].pop()
        self.assertNotEqual(auditor.audit(MODEL, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_duplicate_row_is_rejected(self):
        self.raw["rows"].append(copy.deepcopy(self.raw["rows"][0]))
        self.assertNotEqual(auditor.audit(MODEL, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_each_joint_false_continuation_mutation_is_rejected(self):
        for task_id, lost, context in auditor.WITNESSES:
            with self.subTest(task_id=task_id):
                changed = copy.deepcopy(RAW)
                row = next(r for r in changed["rows"] if (r["task_id"], tuple(r["lost_capabilities"]), r["context"]) == (task_id, lost, context))
                row["tdce_decision"] = "CONTINUE_WITH_LIMITS"
                self.assertNotEqual(auditor.audit(MODEL, changed)["status"], "PASS_METHOD_SCOPED")

    def test_hidden_task_obligation_is_rejected(self):
        changed = copy.deepcopy(MODEL)
        changed["tasks"][1]["obligations"].remove("sibling_unchanged")
        self.assertNotEqual(auditor.audit(changed, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_hidden_focused_window_obligation_is_rejected(self):
        changed = copy.deepcopy(MODEL)
        changed["tasks"][3]["obligations"].remove("active_window_unchanged")
        self.assertNotEqual(auditor.audit(changed, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_forged_compensator_is_rejected(self):
        row = next(r for r in self.raw["rows"] if r["task_id"] == "focused_window_action" and r["context"] == "compensator_missing" and not r["lost_capabilities"])
        row["compensator_available"] = True
        self.assertNotEqual(auditor.audit(MODEL, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_unknown_cause_cannot_become_permissive(self):
        row = next(r for r in self.raw["rows"] if r["task_id"] == "focused_window_action" and r["context"] == "unknown_cause" and not r["lost_capabilities"])
        row["tdce_decision"] = "CONTINUE_WITH_LIMITS"
        self.assertNotEqual(auditor.audit(MODEL, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_expired_allowance_cannot_continue(self):
        row = next(r for r in self.raw["rows"] if r["task_id"] == "focused_window_action" and r["context"] == "degraded_allowance_expired" and r["lost_capabilities"] == ["window_identity"])
        row["tdce_decision"] = "CONTINUE_WITH_LIMITS"
        self.assertNotEqual(auditor.audit(MODEL, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_route_proof_forgery_is_rejected(self):
        changed = copy.deepcopy(MODEL)
        route = next(r for r in changed["tasks"][3]["routes"] if r["route_id"] == "pixel_visual_only")
        route["proves"].append("active_window_unchanged")
        self.assertNotEqual(auditor.audit(changed, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_malformed_loss_set_is_rejected(self):
        self.raw["rows"][0]["lost_capabilities"] = ["forged"]
        self.assertNotEqual(auditor.audit(MODEL, self.raw)["status"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main(verbosity=2)

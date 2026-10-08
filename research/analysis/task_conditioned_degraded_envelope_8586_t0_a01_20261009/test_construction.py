from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import auditor
import candidate


HERE = Path(__file__).parent
MODEL = json.loads((HERE / "model.json").read_text(encoding="utf-8"))


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.raw = {"schema": "TDCE_CANDIDATE_RAW_V1", "rows": candidate.build_rows(MODEL)}

    def test_full_grid_audits_and_exposes_joint_nonadditivity(self):
        result = auditor.audit(MODEL, self.raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED", result["errors"])
        self.assertEqual(result["expected_rows"], 1152)
        self.assertGreater(result["counts"]["edgewise_false_continue"], 0)
        self.assertGreater(result["counts"]["blanket_false_stop"], 0)

    def test_missing_row_is_rejected(self):
        mutated = copy.deepcopy(self.raw)
        mutated["rows"].pop()
        self.assertNotEqual(auditor.audit(MODEL, mutated)["status"], "PASS_METHOD_SCOPED")

    def test_joint_loss_cannot_compose_ineligible_proofs(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["task_id"] == "preserve_sibling_edit" and set(r["lost_capabilities"]) == {"semantic_target", "native_effect_check"} and r["context"] == "valid")
        self.assertEqual(row["edgewise_decision"], "CONTINUE")
        self.assertEqual(row["tdce_decision"], "STOP_UNKNOWN")
        row["tdce_decision"] = "CONTINUE_WITH_LIMITS"
        self.assertNotEqual(auditor.audit(MODEL, mutated)["status"], "PASS_METHOD_SCOPED")

    def test_forged_compensator_is_rejected(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["task_id"] == "preserve_sibling_edit" and r["context"] == "compensator_missing" and not r["lost_capabilities"])
        row["compensator_available"] = True
        self.assertNotEqual(auditor.audit(MODEL, mutated)["status"], "PASS_METHOD_SCOPED")

    def test_hidden_mandatory_gate_is_rejected(self):
        mutated = copy.deepcopy(self.raw)
        mutated["rows"][0]["mandatory_gates"] = ["authority"]
        self.assertNotEqual(auditor.audit(MODEL, mutated)["status"], "PASS_METHOD_SCOPED")

    def test_hidden_task_obligation_is_rejected(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["task_id"] == "preserve_sibling_edit" and r["context"] == "valid" and not r["lost_capabilities"])
        row["task_obligations"].remove("sibling_unchanged")
        self.assertNotEqual(auditor.audit(MODEL, mutated)["status"], "PASS_METHOD_SCOPED")

    def test_forged_route_proof_is_rejected(self):
        mutated_model = copy.deepcopy(MODEL)
        route = next(r for t in mutated_model["tasks"] if t["task_id"] == "preserve_sibling_edit" for r in t["routes"] if r["route_id"] == "preserve_pixel_visual")
        route["proves"].append("sibling_unchanged")
        self.assertNotEqual(auditor.audit(mutated_model, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_weakened_context_contract_is_rejected(self):
        mutated_model = copy.deepcopy(MODEL)
        mutated_model["context_contract"]["unknown_cause"] = "CONTINUE"
        self.assertNotEqual(auditor.audit(mutated_model, self.raw)["status"], "PASS_METHOD_SCOPED")

    def test_expired_allowance_cannot_continue(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["task_id"] == "single_toggle" and r["context"] == "degraded_allowance_expired" and "semantic_target" in r["lost_capabilities"])
        row["tdce_decision"] = "CONTINUE_WITH_LIMITS"
        self.assertNotEqual(auditor.audit(MODEL, mutated)["status"], "PASS_METHOD_SCOPED")

    def test_unknown_cause_cannot_continue(self):
        mutated = copy.deepcopy(self.raw)
        row = next(r for r in mutated["rows"] if r["task_id"] == "single_toggle" and r["context"] == "unknown_cause" and not r["lost_capabilities"])
        row["tdce_decision"] = "CONTINUE_WITH_LIMITS"
        self.assertNotEqual(auditor.audit(MODEL, mutated)["status"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main(verbosity=2)

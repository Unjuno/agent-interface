"""Construction checks; these call policy/auditor functions, not the one-shot runner."""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).resolve().parent


class MethodConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.visible = json.loads((ROOT / "fixture_visible.json").read_text())
        cls.cases = {item["id"]: item for item in cls.visible["cases"]}

    def observation(self, case_id: str, node_id: str, sequence: int = 2) -> dict:
        case = self.cases[case_id]
        node = case["nodes"][node_id]
        result = {"node_id": node_id, "start_id": case["start"], "goal_id": case["goal"],
                  "binding": case["binding"], "epoch": node["epoch"], "sequence": sequence,
                  "edges": node["edges"]}
        if "closure_receipt" in node:
            result["closure_receipt"] = node["closure_receipt"]
        return result

    def state_at_u(self, case_id: str = "blocked_class_gain") -> dict:
        state = candidate.new_state("S")
        state["epoch"] = 1
        state["root_route_tokens"].update({"upper", "lower"})
        state["visited_nodes"].append("U")
        state["path"].append({"from": "S", "to": "U", "edge_id": "su", "route_token": "upper"})
        return state

    def test_valid_certificate_switches_only_to_observed_alternative(self):
        action, evidence = candidate.choose_action(
            self.observation("blocked_class_gain", "U"), self.state_at_u(), "class_aware")
        self.assertEqual(action, {"kind": "BACKTRACK", "reason": "class_switch"})
        self.assertEqual(evidence["kind"], "CLASS_CERTIFICATE_ACCEPTED")
        self.assertEqual(evidence["alternative_tokens"], ["lower"])

    def test_mismatched_binding_is_rejected_and_not_switch(self):
        action, evidence = candidate.choose_action(
            self.observation("unsupported_false_cue", "U"), self.state_at_u("unsupported_false_cue"), "class_aware")
        self.assertEqual(evidence["reason"], "binding_mismatch")
        self.assertNotEqual(action.get("reason"), "class_switch")

    def test_epoch_mismatch_is_rejected(self):
        state = self.state_at_u("dynamic_epoch_invalidation")
        state["epoch"] = 2
        action, evidence = candidate.choose_action(
            self.observation("dynamic_epoch_invalidation", "U"), state, "class_aware")
        self.assertEqual(evidence["reason"], "epoch_mismatch")
        self.assertNotEqual(action.get("reason"), "class_switch")

    def test_oracle_is_not_imported_by_candidate_or_runner(self):
        for name in ("candidate.py", "run_candidate.py"):
            tree = ast.parse((ROOT / name).read_text())
            imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            imports.extend(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                           for alias in node.names)
            self.assertNotIn("oracle", imports)

    def test_path_enumerator_sees_true_block_and_viable_control(self):
        blocked = self.cases["blocked_class_gain"]
        viable = self.cases["viable_same_class"]
        self.assertEqual(audit.graph_paths(blocked, "S", "G", "upper"), [])
        self.assertTrue(audit.graph_paths(viable, "S", "G", "upper"))

    def test_receipt_checks_binding_epoch_and_route(self):
        obs = self.observation("blocked_class_gain", "U")
        self.assertEqual(audit.receipt_status(obs, "upper"), (True, None))
        self.assertEqual(audit.receipt_status(self.observation("unsupported_false_cue", "U"), "upper"),
                         (False, "binding_mismatch"))
        self.assertEqual(audit.receipt_status(self.observation("dynamic_epoch_invalidation", "U"), "upper"),
                         (False, "epoch_mismatch"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
A1 = ROOT / "research/doom/v39_soft_feedback_routing_a01_20261005"
CONTROLLER = ROOT / "research/doom/map01_overlap_controller_v39.py"
A1_RESULT = A1 / "RESULT.json"
FREEZE = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)

for name, path in (("controller", CONTROLLER), ("a01_result", A1_RESULT),
                   ("candidate", PKG / "candidate.py"), ("audit", PKG / "audit.py")):
    require(digest(path) == FREEZE["sha256"][name], f"{name} hash mismatch")
raw = json.loads((PKG / "RESULT.json").read_text(encoding="utf-8"))
a1 = json.loads(A1_RESULT.read_text(encoding="utf-8"))
require(raw["main_base"] == FREEZE["main_base"], "base mismatch")
require(raw["a01_result_sha256"] == digest(A1_RESULT), "A01 raw link mismatch")
summary = raw["summary"]
require(summary == {
    "signal_id": "ammo", "source_value": 46, "current_value": 37,
    "hard_minimum": 1, "soft_event_count": 1, "sequence": 2,
    "observed_during_iteration": 0, "cover_policy_source_iteration": 0,
    "effect": "prior_cover_preserved", "grants_input_authority": False,
}, "summary values or authority scope changed")
require(a1["monitor"]["latest_soft_event"]["signal"]["signal_id"] == "ammo",
        "A01 event is not ammo")
require(raw["planner"]["calls"] == ["begin_turn"] and
        raw["planner"]["prompt_contains_exact_summary"] is True,
        "stub prompt did not carry exact summary")
require('Current locally verified ammo: 37.' in raw["planner"]["prompt"],
        "current ammo field missing")

source = CONTROLLER.read_text(encoding="utf-8")
tree = ast.parse(source)
summary_fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "latest_soft_event_summary")
begin_fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "begin_model_turn")
summary_src = ast.unparse(summary_fn)
begin_src = ast.unparse(begin_fn)
summary_gets = [node for node in ast.walk(summary_fn) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
                and node.args and isinstance(node.args[0], ast.Constant)]
require("decision = decisions[-1]" in summary_src and any(
        node.args[0].value == "cover_validity_latest_soft_event" for node in summary_gets),
        "summary helper no longer selects latest completed decision event")
summary_pairs = {key.value: value.value for node in ast.walk(summary_fn)
                 if isinstance(node, ast.Dict)
                 for key, value in zip(node.keys, node.values)
                 if isinstance(key, ast.Constant) and isinstance(key.value, str)
                 and isinstance(value, ast.Constant)}
require(summary_pairs.get("effect") == "prior_cover_preserved" and
        summary_pairs.get("grants_input_authority") is False,
        "summary helper authority semantics changed")
prompt_uses_summary = any(isinstance(node, ast.Call) and
                          isinstance(node.func, ast.Attribute) and node.func.attr == "dumps"
                          and isinstance(node.func.value, ast.Name) and node.func.value.id == "json"
                          and node.args and isinstance(node.args[0], ast.Name)
                          and node.args[0].id == "prior_soft_event_summary"
                          for node in ast.walk(begin_fn))
planner_begin = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "begin_turn"
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "planner"
                    for node in ast.walk(begin_fn))
require(prompt_uses_summary and planner_begin,
        "prompt builder no longer sends serialized summary to planner")

report = {
    "schema": "v39-soft-next-turn-delivery-audit-a03-v1",
    "checks": {
        "A01_soft_ammo_event_preserved_exactly": True,
        "latest_completed_decision_summary_reconstructed": True,
        "summary_retains_source_current_sequence_floor": True,
        "summary_explicitly_preserves_no_authority": True,
        "actual_prompt_builder_delivers_exact_summary_to_stub": True,
    },
    "disposition": "PASS_NEXT_TURN_DELIVERY; A01_A02_IN_FLIGHT_DELIVERY_FAILURE_REMAINS",
    "scope": "one offline synthetic next-turn prompt-builder construction",
}
(PKG / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
print(json.dumps({"audit": "PASS_A03_RAW_SOURCE_RECONSTRUCTION",
                  "disposition": report["disposition"], "checks": len(report["checks"])},
                 sort_keys=True))

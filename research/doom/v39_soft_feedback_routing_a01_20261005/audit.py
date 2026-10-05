from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
FREEZE = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))
CONTROLLER = ROOT / "research/doom/map01_overlap_controller_v39.py"
GUARD = PKG / "source/observable_signal_guard_v2.py"
RESULT = PKG / "RESULT.json"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def called(node: ast.AST, name: str) -> list[ast.Call]:
    found = []
    for item in ast.walk(node):
        if isinstance(item, ast.Call):
            func = item.func
            if isinstance(func, ast.Name) and func.id == name:
                found.append(item)
            elif isinstance(func, ast.Attribute) and func.attr == name:
                found.append(item)
    return found

def literal_dict_has(node: ast.AST, key: str) -> bool:
    return any(isinstance(item, ast.Dict) and any(
        isinstance(k, ast.Constant) and k.value == key for k in item.keys)
        for item in ast.walk(node))

require(digest(CONTROLLER) == FREEZE["sha256"]["controller"], "controller hash changed")
require(digest(GUARD) == FREEZE["sha256"]["guard_source_copy"], "guard hash changed")
require(digest(PKG / "candidate.py") == FREEZE["sha256"]["candidate"], "candidate hash changed")
require(digest(PKG / "audit.py") == FREEZE["sha256"]["audit"], "audit hash changed")
raw = json.loads(RESULT.read_text(encoding="utf-8"))
require(raw["main_base"] == FREEZE["main_base"], "base mismatch")
require(raw["monitor"]["returned"] is None, "soft observation unexpectedly invalidated")
require(raw["monitor"]["soft_event_count"] == 1, "soft event count mismatch")
event = raw["monitor"]["latest_soft_event"]
require(event["signal"]["signal_id"] == "ammo" and event["signal"]["value"] == 37,
        "ammo soft event mismatch")
require(event["outcome"]["status"] == "SOFT_CHANGED" and
        event["outcome"]["reason"] == "within_validity_envelope" and
        event["outcome"]["requires_new_decision"] is False and
        event["outcome"]["keep_existing_policy"] is True,
        "wrong production guard outcome")
require(raw["monitor"]["policy_invalidation"] is False, "unexpected policy invalidation")
require(raw["pending_planner_stub"]["calls"] == ["begin_turn"], "unexpected planner calls")
require(raw["pending_planner_stub"]["prompt_unchanged_after_observation"] is True,
        "stub prompt changed")

source = CONTROLLER.read_text(encoding="utf-8")
tree = ast.parse(source)
main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
wait_fn = next(node for node in ast.walk(main) if isinstance(node, ast.FunctionDef) and node.name == "wait")
wait_source = ast.unparse(wait_fn)
require("observation_monitor.observe(row)" in wait_source, "monitor not called in wait")
require("if invalidation is not None" in wait_source and "policy_invalidation" in wait_source,
        "wait does not route only non-None monitor results as invalidations")
predicate_return = any(isinstance(node, ast.If) and ast.unparse(node.test) == "predicate(row)"
                       and node.body and isinstance(node.body[0], ast.Return)
                       and ast.unparse(node.body[0].value) == "row"
                       for node in ast.walk(wait_fn))
require(predicate_return, "wait predicate return path changed")

main_source = ast.unparse(main)
prior_calls = called(main, "latest_soft_event_summary")
begin_calls = called(main, "begin_model_turn")
await_calls = called(main, "await_turn")
wait_calls = [call for call in called(main, "wait") if any(
    kw.arg == "observation_monitor" for kw in call.keywords)]
future_result_calls = [call for call in called(main, "result") if isinstance(call.func, ast.Attribute)
                       and call.func.attr == "result"]
require(len(prior_calls) >= 1 and len(begin_calls) == 1 and len(await_calls) == 1,
        "planner timeline anchors missing")
require(any(call.lineno < begin_calls[0].lineno for call in prior_calls),
        "soft summary is not captured before current turn")
require(any(call.lineno > await_calls[0].lineno for call in wait_calls),
        "monitored wait is not inside pending-turn region")
require(len(future_result_calls) == 1, "expected one planner future result join")
post_turn_soft_records = [call for call in called(main, "append")
                          if isinstance(call.func, ast.Attribute) and call.func.attr == "append"
                          and call.lineno > future_result_calls[0].lineno
                          and literal_dict_has(call, "cover_validity_latest_soft_event")]
require(post_turn_soft_records, "no soft-event decision record after planner result")
require("prior_soft_event_summary" in ast.unparse(begin_calls[0]),
        "current planner call does not receive captured summary")
require("latest_soft_event_summary(decisions)" in main_source,
        "subsequent decision summary route missing")

# Independently reconstruct the line ordering from frozen current-main syntax.
report = {
    "schema": "v39-soft-event-routing-audit-a01-v1",
    "candidate_raw_sha256": digest(RESULT),
    "controller_sha256": digest(CONTROLLER),
    "guard_copy_sha256": digest(GUARD),
    "checks": {
        "production_monitor_emits_soft_ammo_change_without_invalidation": True,
        "current_turn_prompt_built_before_pending_wait": True,
        "monitor_observed_inside_pending_turn_wait": True,
        "no_planner_feedback_call_on_soft_event_path": True,
        "soft_event_saved_to_decision_after_future_result": True,
        "summary_available_to_subsequent_turn": True,
    },
    "line_evidence": {
        "soft_summary_line": prior_calls[0].lineno,
        "begin_model_turn_line": begin_calls[0].lineno,
        "planner_await_submit_line": await_calls[0].lineno,
        "pending_monitored_wait_line": min(call.lineno for call in wait_calls),
        "planner_future_result_line": future_result_calls[0].lineno,
        "post_turn_soft_event_record_line": min(call.lineno for call in post_turn_soft_records),
    },
    "disposition": "FAIL_NO_INDEPENDENT_IN_FLIGHT_FEEDBACK",
    "scope": "offline source-composition and synthetic typed-observation only",
}
(PKG / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"audit": "PASS_RAW_AND_SOURCE_RECONSTRUCTION",
                  "scientific_disposition": report["disposition"],
                  "checks": len(report["checks"])}, sort_keys=True))


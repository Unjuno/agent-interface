from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
A1 = ROOT / "research/doom/v39_soft_feedback_routing_a01_20261005"
FREEZE = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))
CONTROLLER = ROOT / "research/doom/map01_overlap_controller_v39.py"
A1_RAW = A1 / "RESULT.json"
A1_FREEZE = A1 / "FREEZE.json"
A1_GUARD = A1 / "source/observable_signal_guard_v2.py"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [item for item in ast.walk(node) if isinstance(item, ast.Call) and
            ((isinstance(item.func, ast.Name) and item.func.id == name) or
             (isinstance(item.func, ast.Attribute) and item.func.attr == name))]

def has_key(node: ast.AST, key: str) -> bool:
    return any(isinstance(item, ast.Dict) and any(
        isinstance(k, ast.Constant) and k.value == key for k in item.keys)
        for item in ast.walk(node))

require(digest(A1_RAW) == FREEZE["a01_result_sha256"], "A01 raw hash mismatch")
require(digest(CONTROLLER) == FREEZE["sha256"]["controller"], "controller hash mismatch")
require(digest(A1_GUARD) == FREEZE["sha256"]["guard_source_copy"], "guard copy hash mismatch")
require(digest(PKG / "audit.py") == FREEZE["sha256"]["audit"], "A02 audit hash mismatch")
raw = json.loads(A1_RAW.read_text(encoding="utf-8"))
require(raw["main_base"] == FREEZE["main_base"], "main base mismatch")
require(raw["monitor"]["returned"] is None, "monitor returned invalidation")
require(raw["monitor"]["soft_event_count"] == 1, "soft event count mismatch")
event = raw["monitor"]["latest_soft_event"]
require(event["signal"]["signal_id"] == "ammo" and
        event["signal"]["value"] == 37 and event["signal"]["sequence"] == 2,
        "ammo event mismatch")
require(event["outcome"]["status"] == "SOFT_CHANGED" and
        event["outcome"]["reason"] == "within_validity_envelope" and
        event["outcome"]["keep_existing_policy"] is True and
        event["outcome"]["requires_new_decision"] is False,
        "production guard outcome mismatch")
require(raw["pending_planner_stub"]["calls"] == ["begin_turn"] and
        raw["pending_planner_stub"]["prompt_unchanged_after_observation"] is True,
        "pending planner stub record mismatch")

source = CONTROLLER.read_text(encoding="utf-8")
tree = ast.parse(source)
main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
wait_fn = next(node for node in ast.walk(main)
               if isinstance(node, ast.FunctionDef) and node.name == "wait")
wait_source = ast.unparse(wait_fn)
require("observation_monitor.observe(row)" in wait_source, "monitor absent from wait")
require("if invalidation is not None" in wait_source and
        "policy_invalidation" in wait_source,
        "wait invalidation route changed")
predicate_return = any(isinstance(node, ast.If) and ast.unparse(node.test) == "predicate(row)"
                       and node.body and isinstance(node.body[0], ast.Return)
                       and ast.unparse(node.body[0].value) == "row"
                       for node in ast.walk(wait_fn))
require(predicate_return, "wait predicate return changed")

prior = calls(main, "latest_soft_event_summary")
begin = calls(main, "begin_model_turn")
submit_await = [node for node in ast.walk(main) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute) and node.func.attr == "submit"
                and node.args and isinstance(node.args[0], ast.Attribute)
                and node.args[0].attr == "await_turn"
                and isinstance(node.args[0].value, ast.Name)
                and node.args[0].value.id == "planner"]
require(len(prior) == 1 and len(begin) == 1 and len(submit_await) == 1,
        "planner timeline anchors missing")
require(prior[0].lineno < begin[0].lineno < submit_await[0].lineno,
        "summary / turn / submit order changed")

pending = [node for node in ast.walk(main) if isinstance(node, ast.While)
           and ast.unparse(node.test) == "not future.done()"]
require(len(pending) == 1, "pending planner loop missing or ambiguous")
pending_loop = pending[0]
monitored_waits = [node for node in calls(pending_loop, "wait") if any(
    keyword.arg == "observation_monitor" for keyword in node.keywords)]
require(len(monitored_waits) == 1, "monitored wait not uniquely inside pending turn")
require(monitored_waits[0].lineno > submit_await[0].lineno,
        "pending wait precedes planner submission")
future_result = [node for node in calls(main, "result")
                 if isinstance(node.func, ast.Attribute) and node.func.attr == "result"
                 and isinstance(node.func.value, ast.Name) and node.func.value.id == "future"]
require(len(future_result) == 1 and future_result[0].lineno > monitored_waits[0].lineno,
        "planner result join missing after monitored wait")
post_turn_records = [node for node in calls(main, "append")
                     if isinstance(node.func, ast.Attribute) and node.func.attr == "append"
                     and node.lineno > future_result[0].lineno
                     and has_key(node, "cover_validity_latest_soft_event")]
require(post_turn_records, "post-turn current-decision soft record missing")

report = {
    "schema": "v39-soft-event-routing-a02-audit-v1",
    "main_base": FREEZE["main_base"],
    "a01_result_sha256": digest(A1_RAW),
    "a01_original_audit_status": "FAIL_TIMELINE_ANCHORS_MISSING",
    "a01_candidate_rerun": False,
    "checks": {
        "production_monitor_soft_ammo_change_has_no_invalidation": True,
        "planner_summary_and_prompt_precede_current_wait": True,
        "soft_observation_is_monitored_inside_pending_turn_loop": True,
        "soft_event_is_recorded_on_decision_after_future_result": True,
        "soft_summary_route_is_later_decision_only": True,
    },
    "line_evidence": {
        "prior_summary_line": prior[0].lineno,
        "begin_model_turn_line": begin[0].lineno,
        "pool_submit_await_method_reference_line": submit_await[0].lineno,
        "pending_loop_line": pending_loop.lineno,
        "monitored_wait_line": monitored_waits[0].lineno,
        "future_result_line": future_result[0].lineno,
        "post_turn_record_line": min(node.lineno for node in post_turn_records),
    },
    "disposition": "PASS_SOURCE_RAW_RECONSTRUCTION; FAIL_NO_INDEPENDENT_IN_FLIGHT_FEEDBACK",
    "scope": "offline synthetic typed-observation and source-composition only",
}
(PKG / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
print(json.dumps({"audit": "PASS_A02_RAW_AND_SOURCE_RECONSTRUCTION",
                  "disposition": report["disposition"],
                  "checks": len(report["checks"])}, sort_keys=True))

#!/usr/bin/env python3
"""Separate raw-only enumerator for Issue #8586; does not import candidate.py."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

ORACLE_TASKS = {
    "single_toggle": {
        "obligations": ["correct_target", "exactly_once", "requested_state"],
        "compensator_required": True,
        "hard_gates": ["target_scope", "freshness", "authority", "independent_effect"],
        "routes": [
            ("toggle_semantic_native", frozenset(("semantic_target", "native_effect_check", "pointer_action")), frozenset(("correct_target", "exactly_once", "requested_state"))),
            ("toggle_pixel_native", frozenset(("pixel_target", "native_effect_check", "pointer_action")), frozenset(("correct_target", "exactly_once", "requested_state"))),
            ("toggle_semantic_visual", frozenset(("semantic_target", "visual_diff", "pointer_action")), frozenset(("correct_target", "exactly_once", "requested_state"))),
            ("toggle_pixel_visual", frozenset(("pixel_target", "visual_diff", "pointer_action")), frozenset(("correct_target", "exactly_once", "requested_state"))),
        ],
    },
    "preserve_sibling_edit": {
        "obligations": ["correct_target", "persisted_after_reopen", "sibling_unchanged", "exactly_once"],
        "compensator_required": True,
        "hard_gates": ["target_scope", "freshness", "authority", "independent_effect"],
        "routes": [
            ("preserve_semantic_native", frozenset(("semantic_target", "native_effect_check", "pointer_action")), frozenset(("correct_target", "persisted_after_reopen", "sibling_unchanged", "exactly_once"))),
            ("preserve_pixel_native", frozenset(("pixel_target", "native_effect_check", "pointer_action")), frozenset(("correct_target", "persisted_after_reopen", "sibling_unchanged", "exactly_once"))),
            ("preserve_semantic_visual", frozenset(("semantic_target", "visual_diff", "pointer_action")), frozenset(("correct_target", "persisted_after_reopen", "sibling_unchanged", "exactly_once"))),
            ("preserve_pixel_visual", frozenset(("pixel_target", "visual_diff", "pointer_action")), frozenset(("correct_target", "persisted_after_reopen", "exactly_once"))),
        ],
    },
    "read_one_value": {
        "obligations": ["correct_target", "value_transcribed"],
        "compensator_required": False,
        "hard_gates": ["target_scope", "freshness", "authority"],
        "routes": [
            ("read_semantic", frozenset(("semantic_target", "read_action")), frozenset(("correct_target", "value_transcribed"))),
            ("read_pixel", frozenset(("pixel_target", "read_action")), frozenset(("correct_target", "value_transcribed"))),
        ],
    },
}
PRIMARY_REQUIREMENTS = frozenset(("semantic_target", "native_effect_check"))
PER_CAPABILITY_REPLACEMENTS = {
    "semantic_target": "pixel_target",
    "native_effect_check": "visual_diff",
}
UNIVERSAL_HARD_GATES = ["target_scope", "freshness", "authority"]
EXPECTED_CAPABILITIES = ["semantic_target", "native_effect_check", "pixel_target", "visual_diff", "pointer_action", "read_action"]
CONTEXTS = (
    "valid", "unknown_cause", "stale_configuration", "compensator_missing",
    "task_intent_changed", "degraded_allowance_expired",
)
EXPECTED_CONTEXT_CONTRACT = {
    "unknown_cause": "STOP_UNKNOWN",
    "stale_configuration": "STOP_UNKNOWN",
    "task_intent_changed": "STOP_UNKNOWN",
    "compensator_missing": "STOP_UNKNOWN when task requires a compensator; otherwise not applicable",
    "degraded_allowance_expired": "STOP_UNKNOWN when a task-relevant primary capability is lost; otherwise not applicable",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_context(task: dict, context: str, degraded: bool) -> bool:
    if context in ("unknown_cause", "stale_configuration", "task_intent_changed"):
        return False
    if context == "compensator_missing" and task["compensator_required"]:
        return False
    if context == "degraded_allowance_expired" and degraded:
        return False
    return True


def expected_grid(model: dict) -> dict[tuple[str, tuple[str, ...], str], dict]:
    all_caps = set(EXPECTED_CAPABILITIES)
    output = {}
    for task_name, task in ORACLE_TASKS.items():
        primary_route = task["routes"][0][1]
        for n in range(len(EXPECTED_CAPABILITIES) + 1):
            for lost_tuple in itertools.combinations(EXPECTED_CAPABILITIES, n):
                lost = set(lost_tuple)
                available = all_caps - lost
                degraded = not (primary_route <= available)
                for context in CONTEXTS:
                    eligible = safe_context(task, context, degraded)
                    feasible_route = next((r for r in task["routes"] if r[1] <= available and set(task["obligations"]) <= r[2]), None) if eligible else None
                    # Reconstruct the intentionally naive independent-edge baseline.
                    fallback_route = []
                    for required in task["routes"][0][1]:
                        substitute = required
                        if required in PER_CAPABILITY_REPLACEMENTS and required not in available:
                            substitute = PER_CAPABILITY_REPLACEMENTS[required]
                        fallback_route.append(substitute)
                    edgewise = "CONTINUE" if eligible and set(fallback_route) <= available else "STOP"
                    if not eligible:
                        edgewise = "STOP_UNKNOWN"
                    blanket = "CONTINUE" if eligible and not lost else "STOP"
                    if feasible_route is None:
                        decision = "STOP_UNKNOWN"
                    else:
                        decision = "CONTINUE_WITH_LIMITS"
                    output[(task_name, tuple(sorted(lost)), context)] = {
                        "available_capabilities": sorted(available),
                        "degraded": degraded,
                        "compensator_required": task["compensator_required"],
                        "compensator_available": context != "compensator_missing",
                        "loss_cause_known": context != "unknown_cause",
                        "configuration_fresh": context != "stale_configuration",
                        "task_intent_current": context != "task_intent_changed",
                        "envelope_expired": context == "degraded_allowance_expired" and degraded,
                        "task_obligations": task["obligations"],
                        "mandatory_gates": sorted(set(UNIVERSAL_HARD_GATES) | set(task["hard_gates"])),
                        "edgewise_decision": edgewise,
                        "edgewise_route": sorted(fallback_route) if edgewise in ("CONTINUE", "CONTINUE_WITH_LIMITS") else sorted(fallback_route),
                        "blanket_decision": blanket,
                        "tdce_decision": decision,
                        "tdce_route": feasible_route[0] if feasible_route is not None else None,
                    }
    return output


def audit(model: dict, raw: dict) -> dict:
    errors: list[str] = []
    if raw.get("schema") != "TDCE_CANDIDATE_RAW_V1":
        errors.append("candidate schema mismatch")
    if model.get("capabilities") != EXPECTED_CAPABILITIES:
        errors.append("capability universe mismatch")
    if model.get("universal_hard_gates") != UNIVERSAL_HARD_GATES:
        errors.append("universal hard gates mismatch")
    if tuple(model.get("contexts", [])) != CONTEXTS or model.get("context_contract") != EXPECTED_CONTEXT_CONTRACT:
        errors.append("context contract mismatch")
    model_tasks = {t.get("task_id"): t for t in model.get("tasks", [])}
    if set(model_tasks) != set(ORACLE_TASKS):
        errors.append("task universe mismatch")
    for task_name, oracle_task in ORACLE_TASKS.items():
        task = model_tasks.get(task_name)
        if task is None:
            continue
        if task.get("obligations") != oracle_task["obligations"] or task.get("hard_gates") != oracle_task["hard_gates"]:
            errors.append(f"{task_name}: task contract mismatch")
        model_routes = {r.get("route_id"): r for r in task.get("routes", [])}
        if set(model_routes) != {r[0] for r in oracle_task["routes"]}:
            errors.append(f"{task_name}: route universe mismatch")
            continue
        for route_id, capability_set, proof_set in oracle_task["routes"]:
            entry = model_routes[route_id]
            if set(entry.get("capabilities", [])) != capability_set or set(entry.get("proves", [])) != proof_set:
                errors.append(f"{task_name}/{route_id}: route contract mismatch")
    expected = expected_grid(model)
    seen = set()
    counts = {
        "edgewise_false_continue": 0,
        "joint_loss_false_continue": 0,
        "blanket_false_stop": 0,
        "tdce_feasible_rows": 0,
        "tdce_false_stop": 0,
        "tdce_false_continue": 0,
        "tdce_mismatch": 0,
    }
    for row in raw.get("rows", []):
        key = (row.get("task_id"), tuple(row.get("lost_capabilities", [])), row.get("context"))
        if key in seen:
            errors.append(f"duplicate row: {key}")
            continue
        seen.add(key)
        oracle = expected.get(key)
        if oracle is None:
            errors.append(f"out-of-grid row: {key}")
            continue
        for field, value in oracle.items():
            if row.get(field) != value:
                errors.append(f"{key}: {field} mismatch")
        truth_continue = oracle["tdce_decision"] == "CONTINUE_WITH_LIMITS"
        if truth_continue:
            counts["tdce_feasible_rows"] += 1
        if row.get("edgewise_decision") in ("CONTINUE", "CONTINUE_WITH_LIMITS") and not truth_continue:
            counts["edgewise_false_continue"] += 1
            if key[0] == "preserve_sibling_edit" and len(key[1]) >= 2:
                counts["joint_loss_false_continue"] += 1
        if row.get("blanket_decision") == "STOP" and truth_continue:
            counts["blanket_false_stop"] += 1
        if row.get("tdce_decision") != oracle["tdce_decision"]:
            counts["tdce_mismatch"] += 1
            if row.get("tdce_decision") == "STOP_UNKNOWN" and truth_continue:
                counts["tdce_false_stop"] += 1
            if row.get("tdce_decision") == "CONTINUE_WITH_LIMITS" and not truth_continue:
                counts["tdce_false_continue"] += 1
    if seen != set(expected):
        errors.append(f"row coverage mismatch: expected={len(expected)} seen={len(seen)}")
    target = ("preserve_sibling_edit", ("native_effect_check", "semantic_target"), "valid")
    witness = next((r for r in raw.get("rows", []) if (r.get("task_id"), tuple(r.get("lost_capabilities", [])), r.get("context")) == target), None)
    if witness is None or witness.get("edgewise_decision") not in ("CONTINUE", "CONTINUE_WITH_LIMITS") or witness.get("tdce_decision") != "STOP_UNKNOWN":
        errors.append("joint-loss counterexample absent")
    elif counts["joint_loss_false_continue"] == 0:
        errors.append("edgewise baseline has no joint-loss false continuation")
    if not any(c == "valid" and lost and r["tdce_decision"] == "CONTINUE_WITH_LIMITS" and r["blanket_decision"] == "STOP" for (t, lost, c), r in expected.items()):
        errors.append("blanket-stop feasible case absent")
    return {
        "schema": "TDCE_AUDIT_V1",
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "rows": len(raw.get("rows", [])),
        "expected_rows": len(expected),
        "counts": counts,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("candidate_raw", type=Path)
    parser.add_argument("audit_output", type=Path)
    args = parser.parse_args()
    freeze_path = Path(__file__).with_name("FREEZE.json")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze_sha256 = sha256(freeze_path)
    provenance_errors = []
    for name, digest in freeze["frozen_files"].items():
        if sha256(freeze_path.parent / name) != digest:
            provenance_errors.append(f"frozen source digest mismatch: {name}")
    if args.model.resolve() != (freeze_path.parent / "model.json").resolve():
        provenance_errors.append("formal model path does not resolve to frozen package model.json")
    raw = json.loads(args.candidate_raw.read_text(encoding="utf-8"))
    expected_provenance = {
        "allocation_id": freeze["allocation_id"],
        "main_commit": freeze["main_commit"],
        "freeze_sha256": freeze_sha256,
        "model_sha256": sha256(args.model),
        "candidate_sha256": freeze["frozen_files"]["candidate.py"],
    }
    if raw.get("provenance") != expected_provenance:
        provenance_errors.append("candidate raw provenance mismatch")
    result = audit(json.loads(args.model.read_text(encoding="utf-8")), raw)
    result["provenance"] = {
        "allocation_id": freeze["allocation_id"],
        "main_commit": freeze["main_commit"],
        "freeze_sha256": freeze_sha256,
        "model_sha256": sha256(args.model),
        "candidate_sha256": freeze["frozen_files"]["candidate.py"],
        "auditor_sha256": sha256(Path(__file__)),
    }
    if provenance_errors:
        result["errors"].extend(provenance_errors)
        result["status"] = "FAIL_METHOD"
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": result["rows"], "errors": len(result["errors"])}))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independent raw-only oracle for Issue #8586 T0 A02; never imports candidate."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path


ORACLE_TASKS = {
    "single_toggle": {
        "capabilities": ["semantic_target", "native_effect_check", "pixel_target", "visual_diff"],
        "obligations": ["correct_target", "exactly_once", "requested_state"],
        "compensator_required": True,
        "hard_gates": ["independent_effect"],
        "primary_route": ["semantic_target", "native_effect_check"],
        "fallbacks": {"semantic_target": "pixel_target", "native_effect_check": "visual_diff"},
        "routes": [
            ("toggle_semantic_native", ["semantic_target", "native_effect_check"], ["correct_target", "exactly_once", "requested_state"]),
            ("toggle_pixel_native", ["pixel_target", "native_effect_check"], ["correct_target", "exactly_once", "requested_state"]),
            ("toggle_semantic_visual", ["semantic_target", "visual_diff"], ["correct_target", "exactly_once", "requested_state"]),
            ("toggle_pixel_visual", ["pixel_target", "visual_diff"], ["correct_target", "exactly_once", "requested_state"]),
        ],
    },
    "preserve_sibling_edit": {
        "capabilities": ["semantic_target", "native_effect_check", "pixel_target", "visual_diff"],
        "obligations": ["correct_target", "persisted_after_reopen", "sibling_unchanged", "exactly_once"],
        "compensator_required": True,
        "hard_gates": ["independent_effect"],
        "primary_route": ["semantic_target", "native_effect_check"],
        "fallbacks": {"semantic_target": "pixel_target", "native_effect_check": "visual_diff"},
        "routes": [
            ("preserve_semantic_native", ["semantic_target", "native_effect_check"], ["correct_target", "persisted_after_reopen", "sibling_unchanged", "exactly_once"]),
            ("preserve_pixel_native", ["pixel_target", "native_effect_check"], ["correct_target", "persisted_after_reopen", "sibling_unchanged", "exactly_once"]),
            ("preserve_semantic_visual", ["semantic_target", "visual_diff"], ["correct_target", "persisted_after_reopen", "sibling_unchanged", "exactly_once"]),
            ("preserve_pixel_visual", ["pixel_target", "visual_diff"], ["correct_target", "persisted_after_reopen", "exactly_once"]),
        ],
    },
    "read_one_value": {
        "capabilities": ["semantic_target", "pixel_target", "read_action"],
        "obligations": ["correct_target", "value_transcribed"],
        "compensator_required": False,
        "hard_gates": [],
        "primary_route": ["semantic_target", "read_action"],
        "fallbacks": {"semantic_target": "pixel_target"},
        "routes": [
            ("read_semantic", ["semantic_target", "read_action"], ["correct_target", "value_transcribed"]),
            ("read_pixel", ["pixel_target", "read_action"], ["correct_target", "value_transcribed"]),
        ],
    },
    "focused_window_action": {
        "capabilities": ["window_identity", "focus_stability", "pixel_target", "visual_diff"],
        "obligations": ["correct_target", "active_window_unchanged", "exactly_once"],
        "compensator_required": True,
        "hard_gates": ["independent_effect"],
        "primary_route": ["window_identity", "focus_stability"],
        "fallbacks": {"window_identity": "pixel_target", "focus_stability": "visual_diff"},
        "routes": [
            ("window_identity_stable_focus", ["window_identity", "focus_stability"], ["correct_target", "active_window_unchanged", "exactly_once"]),
            ("window_identity_visual_check", ["window_identity", "visual_diff"], ["correct_target", "active_window_unchanged", "exactly_once"]),
            ("pixel_target_stable_focus", ["pixel_target", "focus_stability"], ["correct_target", "active_window_unchanged", "exactly_once"]),
            ("pixel_visual_only", ["pixel_target", "visual_diff"], ["correct_target", "exactly_once"]),
        ],
    },
}
UNIVERSAL_GATES = ["target_scope", "freshness", "authority", "actuation_available"]
CONTEXTS = [
    "valid", "unknown_cause", "stale_configuration", "compensator_missing",
    "task_intent_changed", "degraded_allowance_expired",
]
CONTEXT_CONTRACT = {
    "unknown_cause": "STOP_UNKNOWN",
    "stale_configuration": "STOP_UNKNOWN",
    "task_intent_changed": "STOP_UNKNOWN",
    "compensator_missing": "STOP_UNKNOWN when task requires a compensator; otherwise not applicable",
    "degraded_allowance_expired": "STOP_UNKNOWN when a task-relevant primary capability is lost; otherwise not applicable",
}
WITNESSES = [
    ("preserve_sibling_edit", ("native_effect_check", "semantic_target"), "valid"),
    ("focused_window_action", ("focus_stability", "window_identity"), "valid"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _context_safe(task: dict, context: str, degraded: bool) -> bool:
    if context in {"unknown_cause", "stale_configuration", "task_intent_changed"}:
        return False
    if context == "compensator_missing" and task["compensator_required"]:
        return False
    return not (context == "degraded_allowance_expired" and degraded)


def _expected_decision(task: dict, available: set[str], context: str, degraded: bool):
    safe = _context_safe(task, context, degraded)
    primary = task["primary_route"]
    substitutions = [task["fallbacks"].get(c, c) if c not in available else c for c in primary]
    edgewise = "CONTINUE" if safe and set(substitutions) <= available else "STOP"
    if not safe:
        edgewise = "STOP_UNKNOWN"
    blanket = "CONTINUE" if safe and set(task["capabilities"]) <= available else "STOP"
    route = next(
        (r for r in task["routes"] if set(r[1]) <= available and set(task["obligations"]) <= set(r[2])),
        None,
    ) if safe else None
    if route is not None:
        route = {"route_id": route[0], "capabilities": route[1], "proves": route[2]}
    return edgewise, sorted(substitutions), blanket, "CONTINUE_WITH_LIMITS" if route else "STOP_UNKNOWN", route


def expected_grid() -> dict:
    grid = {}
    for task_id, task in ORACLE_TASKS.items():
        caps = task["capabilities"]
        all_caps = set(caps)
        primary = set(task["primary_route"])
        for n in range(len(caps) + 1):
            for lost_tuple in itertools.combinations(caps, n):
                lost = set(lost_tuple)
                available = all_caps - lost
                degraded = not primary <= available
                for context in CONTEXTS:
                    edgewise, edge_route, blanket, tdce, route = _expected_decision(task, available, context, degraded)
                    key = (task_id, tuple(sorted(lost)), context)
                    grid[key] = {
                        "capability_universe": caps,
                        "available_capabilities": sorted(available),
                        "degraded": degraded,
                        "compensator_required": task["compensator_required"],
                        "compensator_available": context != "compensator_missing",
                        "loss_cause_known": context != "unknown_cause",
                        "configuration_fresh": context != "stale_configuration",
                        "task_intent_current": context != "task_intent_changed",
                        "envelope_expired": context == "degraded_allowance_expired" and degraded,
                        "task_obligations": task["obligations"],
                        "mandatory_gates": sorted(set(UNIVERSAL_GATES) | set(task["hard_gates"])),
                        "edgewise_decision": edgewise,
                        "edgewise_route": edge_route,
                        "blanket_decision": blanket,
                        "tdce_decision": tdce,
                        "tdce_route": route["route_id"] if route else None,
                    }
    return grid


def audit(model: dict, raw: dict) -> dict:
    errors = []
    if raw.get("schema") != "TDCE_A02_CANDIDATE_RAW_V1":
        errors.append("candidate schema mismatch")
    if model.get("universal_hard_gates") != UNIVERSAL_GATES:
        errors.append("universal hard gates mismatch")
    if model.get("contexts") != CONTEXTS or model.get("context_contract") != CONTEXT_CONTRACT:
        errors.append("context contract mismatch")
    model_tasks = {t.get("task_id"): t for t in model.get("tasks", [])}
    if set(model_tasks) != set(ORACLE_TASKS):
        errors.append("task universe mismatch")
    for task_id, oracle in ORACLE_TASKS.items():
        task = model_tasks.get(task_id)
        if task is None:
            continue
        for field in ("capabilities", "obligations", "compensator_required", "hard_gates", "primary_route", "fallbacks"):
            if task.get(field) != oracle[field]:
                errors.append(f"{task_id}: {field} mismatch")
        actual_routes = {r.get("route_id"): r for r in task.get("routes", [])}
        expected_routes = {r[0]: {"route_id": r[0], "capabilities": r[1], "proves": r[2]} for r in oracle["routes"]}
        if actual_routes != expected_routes:
            errors.append(f"{task_id}: route universe or proof mismatch")

    grid = expected_grid()
    seen = set()
    counts = {"edgewise_false_continue": 0, "blanket_false_stop": 0, "tdce_feasible_rows": 0,
              "tdce_false_stop": 0, "tdce_false_continue": 0, "tdce_mismatch": 0}
    false_joint_configs = set()
    rows = raw.get("rows", [])
    for row in rows:
        task_id = row.get("task_id")
        lost = row.get("lost_capabilities")
        context = row.get("context")
        if type(lost) is not list or lost != sorted(set(lost)):
            errors.append("malformed or noncanonical loss set")
            continue
        key = (task_id, tuple(lost), context)
        if key in seen:
            errors.append(f"duplicate row: {key}")
            continue
        seen.add(key)
        expected = grid.get(key)
        if expected is None:
            errors.append(f"out-of-grid row: {key}")
            continue
        for field, value in expected.items():
            if row.get(field) != value:
                errors.append(f"{key}: {field} mismatch")
        is_feasible = expected["tdce_decision"] == "CONTINUE_WITH_LIMITS"
        if is_feasible:
            counts["tdce_feasible_rows"] += 1
        if expected["edgewise_decision"] in ("CONTINUE", "CONTINUE_WITH_LIMITS") and not is_feasible:
            counts["edgewise_false_continue"] += 1
            if len(lost) == 2:
                false_joint_configs.add((task_id, tuple(lost)))
        if expected["blanket_decision"] == "STOP" and is_feasible:
            counts["blanket_false_stop"] += 1
        if row.get("tdce_decision") != expected["tdce_decision"]:
            counts["tdce_mismatch"] += 1
            if row.get("tdce_decision") == "STOP_UNKNOWN" and is_feasible:
                counts["tdce_false_stop"] += 1
            if row.get("tdce_decision") == "CONTINUE_WITH_LIMITS" and not is_feasible:
                counts["tdce_false_continue"] += 1
    if seen != set(grid):
        errors.append(f"row coverage mismatch: expected={len(grid)} seen={len(seen)}")
    counts["distinct_two_capability_joint_false_continuations"] = len(false_joint_configs)
    expected_witnesses = { (t, lost) for t, lost, _ in WITNESSES }
    if not expected_witnesses <= false_joint_configs:
        errors.append("both distinct joint-loss witnesses are not present")
    if counts["distinct_two_capability_joint_false_continuations"] < 2:
        errors.append("fewer than two distinct two-capability false-continuation configurations")
    if counts["edgewise_false_continue"] < 2:
        errors.append("edgewise comparator did not expose two false continuations")
    if counts["blanket_false_stop"] < 1:
        errors.append("blanket-stop comparator has no feasible false stop")
    if counts["tdce_false_continue"] or counts["tdce_false_stop"] or counts["tdce_mismatch"]:
        errors.append("TDCE differs from finite oracle")
    return {"schema": "TDCE_A02_AUDIT_V1", "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
            "rows": len(rows), "expected_rows": len(grid), "counts": counts, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("candidate_raw", type=Path)
    parser.add_argument("audit_output", type=Path)
    args = parser.parse_args()
    freeze_path = Path(__file__).with_name("FREEZE.json")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    digest_errors = [name for name, digest in freeze["frozen_files"].items() if sha256(freeze_path.parent / name) != digest]
    if digest_errors:
        raise SystemExit("frozen file hash mismatch: " + ", ".join(digest_errors))
    if args.model.resolve() != (freeze_path.parent / "model.json").resolve():
        raise SystemExit("formal model path is not the frozen package model")
    raw = json.loads(args.candidate_raw.read_text(encoding="utf-8"))
    expected_provenance = {"allocation_id": freeze["allocation_id"], "main_commit": freeze["main_commit"],
                           "freeze_sha256": sha256(freeze_path), "model_sha256": sha256(args.model),
                           "candidate_sha256": freeze["frozen_files"]["candidate.py"]}
    provenance_errors = [] if raw.get("provenance") == expected_provenance else ["candidate provenance mismatch"]
    result = audit(json.loads(args.model.read_text(encoding="utf-8")), raw)
    result["provenance"] = {"allocation_id": freeze["allocation_id"], "main_commit": freeze["main_commit"],
                            "freeze_sha256": sha256(freeze_path), "model_sha256": sha256(args.model),
                            "candidate_sha256": freeze["frozen_files"]["candidate.py"],
                            "raw_sha256": sha256(args.candidate_raw), "auditor_sha256": sha256(Path(__file__))}
    if provenance_errors:
        result["errors"].extend(provenance_errors)
        result["status"] = "FAIL_METHOD"
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": result["rows"], "errors": len(result["errors"])}))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

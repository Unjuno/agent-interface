#!/usr/bin/env python3
"""Exhaustive candidate for Issue #8586's finite task/capability model."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

PRIMARY = {"semantic_target", "native_effect_check"}
FALLBACK = {
    "semantic_target": "pixel_target",
    "native_effect_check": "visual_diff",
}


def load_model(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(model_path: Path) -> tuple[dict, str]:
    freeze_path = Path(__file__).with_name("FREEZE.json")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    expected = freeze["frozen_files"]
    for name, digest in expected.items():
        source = freeze_path.parent / name
        if sha256(source) != digest:
            raise ValueError(f"frozen source digest mismatch: {name}")
    if model_path.resolve() != (freeze_path.parent / "model.json").resolve():
        raise ValueError("formal model path must be the frozen package model.json")
    return freeze, sha256(freeze_path)


def context_allows(task: dict, context: str, degraded: bool) -> bool:
    if context in {"unknown_cause", "stale_configuration", "task_intent_changed"}:
        return False
    if context == "compensator_missing" and task["compensator_required"]:
        return False
    if context == "degraded_allowance_expired" and degraded:
        return False
    return True


def edgewise_decision(task: dict, available: set[str]) -> tuple[str, list[str]]:
    """Select per-capability fallbacks without checking joint route qualification."""
    selected: list[str] = []
    feasible = True
    for capability in task["routes"][0]["capabilities"]:
        replacement = capability
        if capability in PRIMARY and capability not in available:
            replacement = FALLBACK[capability]
        if replacement not in available:
            feasible = False
        selected.append(replacement)
    return ("CONTINUE" if feasible else "STOP"), selected


def tdce_decision(task: dict, available: set[str], context: str, degraded: bool) -> tuple[str, dict | None]:
    if not context_allows(task, context, degraded):
        return "STOP_UNKNOWN", None
    required_proofs = set(task["obligations"])
    for route in task["routes"]:
        if set(route["capabilities"]) <= available and required_proofs <= set(route["proves"]):
            return "CONTINUE_WITH_LIMITS", route
    return "STOP_UNKNOWN", None


def build_rows(model: dict) -> list[dict]:
    capabilities = model["capabilities"]
    rows: list[dict] = []
    for task in model["tasks"]:
        primary_route = set(task["routes"][0]["capabilities"])
        for count in range(len(capabilities) + 1):
            for lost_tuple in itertools.combinations(capabilities, count):
                lost = set(lost_tuple)
                available = set(capabilities) - lost
                degraded = not (primary_route <= available)
                for context in model["contexts"]:
                    effective_context = context_allows(task, context, degraded)
                    baseline, baseline_route = edgewise_decision(task, available)
                    if not effective_context:
                        baseline = "STOP_UNKNOWN"
                    blanket = "CONTINUE" if not lost and effective_context else "STOP"
                    tdce, route = tdce_decision(task, available, context, degraded)
                    rows.append({
                        "task_id": task["task_id"],
                        "lost_capabilities": sorted(lost),
                        "available_capabilities": sorted(available),
                        "context": context,
                        "degraded": degraded,
                        "compensator_required": task["compensator_required"],
                        "compensator_available": context != "compensator_missing",
                        "loss_cause_known": context != "unknown_cause",
                        "configuration_fresh": context != "stale_configuration",
                        "task_intent_current": context != "task_intent_changed",
                        "envelope_expired": context == "degraded_allowance_expired" and degraded,
                        "task_obligations": task["obligations"],
                        "mandatory_gates": sorted(set(model["universal_hard_gates"]) | set(task["hard_gates"])),
                        "edgewise_decision": baseline,
                        "edgewise_route": sorted(baseline_route),
                        "blanket_decision": blanket,
                        "tdce_decision": tdce,
                        "tdce_route": route["route_id"] if route is not None else None,
                    })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    freeze, freeze_sha256 = verify_freeze(args.model)
    model = load_model(args.model)
    rows = build_rows(model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = {
        "schema": "TDCE_CANDIDATE_RAW_V1",
        "provenance": {
            "allocation_id": freeze["allocation_id"],
            "main_commit": freeze["main_commit"],
            "freeze_sha256": freeze_sha256,
            "model_sha256": sha256(args.model),
            "candidate_sha256": sha256(Path(__file__)),
        },
        "rows": rows,
    }
    args.output.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "rows": len(rows), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

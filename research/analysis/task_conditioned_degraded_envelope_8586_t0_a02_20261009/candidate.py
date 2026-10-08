#!/usr/bin/env python3
"""One-shot candidate enumerator for Issue #8586 T0 A02."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def context_allows(task: dict, context: str, degraded: bool) -> bool:
    if context in ("unknown_cause", "stale_configuration", "task_intent_changed"):
        return False
    if context == "compensator_missing" and task["compensator_required"]:
        return False
    if context == "degraded_allowance_expired" and degraded:
        return False
    return True


def decisions(task: dict, available: set[str], context: str, degraded: bool):
    safe = context_allows(task, context, degraded)
    fallback_route = []
    for capability in task["primary_route"]:
        selected = capability
        if capability not in available:
            selected = task["fallbacks"].get(capability, capability)
        fallback_route.append(selected)
    edgewise = "CONTINUE" if safe and set(fallback_route) <= available else "STOP"
    if not safe:
        edgewise = "STOP_UNKNOWN"

    blanket = "CONTINUE" if safe and not (set(task["capabilities"]) - available) else "STOP"

    qualified = next(
        (
            route
            for route in task["routes"]
            if set(route["capabilities"]) <= available
            and set(task["obligations"]) <= set(route["proves"])
        ),
        None,
    ) if safe else None
    tdce = "CONTINUE_WITH_LIMITS" if qualified is not None else "STOP_UNKNOWN"
    return edgewise, sorted(fallback_route), blanket, tdce, qualified


def build_rows(model: dict) -> list[dict]:
    rows = []
    contexts = model["contexts"]
    for task in model["tasks"]:
        capabilities = task["capabilities"]
        all_capabilities = set(capabilities)
        primary = set(task["primary_route"])
        for count in range(len(capabilities) + 1):
            for lost_tuple in itertools.combinations(capabilities, count):
                lost = set(lost_tuple)
                available = all_capabilities - lost
                degraded = not primary <= available
                for context in contexts:
                    edgewise, edgewise_route, blanket, tdce, route = decisions(
                        task, available, context, degraded
                    )
                    rows.append(
                        {
                            "task_id": task["task_id"],
                            "capability_universe": capabilities,
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
                            "mandatory_gates": sorted(
                                set(model["universal_hard_gates"]) | set(task["hard_gates"])
                            ),
                            "edgewise_decision": edgewise,
                            "edgewise_route": edgewise_route,
                            "blanket_decision": blanket,
                            "tdce_decision": tdce,
                            "tdce_route": route["route_id"] if route is not None else None,
                        }
                    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    model = json.loads(args.model.read_text(encoding="utf-8"))
    freeze_path = Path(__file__).with_name("FREEZE.json")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for name, digest in freeze["frozen_files"].items():
        if sha256(freeze_path.parent / name) != digest:
            raise SystemExit(f"frozen source mismatch: {name}")
    if args.model.resolve() != (freeze_path.parent / "model.json").resolve():
        raise SystemExit("formal model path is not the frozen package model")
    freeze_digest = sha256(freeze_path)
    raw = {
        "schema": "TDCE_A02_CANDIDATE_RAW_V1",
        "provenance": {
            "allocation_id": freeze["allocation_id"],
            "main_commit": freeze["main_commit"],
            "freeze_sha256": freeze_digest,
            "model_sha256": sha256(args.model),
            "candidate_sha256": freeze["frozen_files"]["candidate.py"],
        },
        "rows": build_rows(model),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "rows": len(raw["rows"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

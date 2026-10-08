#!/usr/bin/env python3
"""Independent stdlib-only structural audit for the #4448 construction pilot."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics
import tempfile


def audit(result: dict) -> list[str]:
    errors: list[str] = []
    if result.get("allocation") != "issue4448-construction-pilot-04":
        errors.append("allocation")
    if result.get("classification") != "CONSTRUCTION_ONLY_NOT_FORMAL":
        errors.append("classification")
    arms = {item.get("arm"): item for item in result.get("arms", [])}
    if set(arms) != {"ephemeral", "resident"}:
        return errors + ["arm_set"]
    for arm_name, arm in arms.items():
        actions = arm.get("actions", [])
        records = arm.get("effect_records", [])
        if len(actions) != 4 or len(records) != 4:
            errors.append(f"{arm_name}_count")
        expected_record_sequence = [0, 0, 0, 0] if arm_name == "ephemeral" else list(range(4))
        if [r.get("sequence") for r in records] != expected_record_sequence:
            errors.append(f"{arm_name}_sequence")
        if any(r.get("arm") != arm_name for r in records):
            errors.append(f"{arm_name}_record_arm")
        if not arm.get("release_verified") or any(not a.get("keymap_neutral") for a in actions):
            errors.append(f"{arm_name}_release")
        if [a.get("sequence") for a in actions] != list(range(4)):
            errors.append(f"{arm_name}_action_sequence")
        if any(a.get("xterm_exit") != 0 for a in actions):
            errors.append(f"{arm_name}_exit")
        if any(a.get("next_ready_ns", 0) < a.get("effect_observed_ns", 0) for a in actions):
            errors.append(f"{arm_name}_time_order")
        if any(a.get("effect_to_next_ready_ns") !=
               a.get("next_ready_ns", 0) - a.get("effect_observed_ns", 0) for a in actions):
            errors.append(f"{arm_name}_latency_recompute")
        if [r.get("pid") for r in records] != arm.get("child_pids"):
            errors.append(f"{arm_name}_child_pid_receipt")
        if [a.get("xterm_pid") for a in actions] != (
            arm.get("xterm_pids", []) if arm_name == "ephemeral" else arm.get("xterm_pids", []) * 4
        ):
            errors.append(f"{arm_name}_xterm_pid_receipt")
        if arm_name == "resident" and [a.get("child_pid") for a in actions] != [r.get("pid") for r in records]:
            errors.append("resident_action_child_pid_receipt")
        if arm.get("session_wall_ns") != arm.get("session_end_ns", 0) - arm.get("session_start_ns", 0):
            errors.append(f"{arm_name}_session_recompute")
        if len(actions) == 4 and len(records) == 4:
            if arm_name == "ephemeral":
                if len(set(arm.get("xterm_pids", []))) != 4 or len(set(arm.get("child_pids", []))) != 4:
                    errors.append("ephemeral_not_fresh")
                if arm.get("xterm_exits") != [0, 0, 0, 0]:
                    errors.append("ephemeral_exit_list")
            else:
                if len(set(arm.get("xterm_pids", []))) != 1 or len(set(arm.get("child_pids", []))) != 1:
                    errors.append("resident_not_reused")
                if not all(a.get("xterm_and_child_still_live") for a in actions):
                    errors.append("resident_not_live")
                if arm.get("xterm_exits") != [0]:
                    errors.append("resident_exit_list")
    if result.get("arm_order") != ["ephemeral", "resident"]:
        errors.append("arm_order")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.result.read_bytes()
    result = json.loads(raw)
    errors = audit(result)
    corruptions = {}
    mutations = {
        "effect_sequence": lambda x: x["arms"][0]["effect_records"][0].update(sequence=9),
        "release": lambda x: x["arms"][1]["actions"][0].update(keymap_neutral=False),
        "child_identity": lambda x: x["arms"][1]["effect_records"][1].update(pid=999999),
        "latency": lambda x: x["arms"][1]["actions"][0].update(effect_to_next_ready_ns=0),
        "process_exit": lambda x: x["arms"][0]["actions"][0].update(xterm_exit=9),
    }
    for name, mutate in mutations.items():
        damaged = copy.deepcopy(result)
        mutate(damaged)
        corruptions[name] = bool(audit(damaged))
    latencies = {
        arm["arm"]: [a["effect_to_next_ready_ns"] for a in arm["actions"]]
        for arm in result["arms"]
    }
    summary = {
        "allocation": result.get("allocation"),
        "result_sha256": hashlib.sha256(raw).hexdigest(),
        "errors": errors,
        "corruption_controls": corruptions,
        "corruption_rejected": sum(corruptions.values()),
        "corruption_total": len(corruptions),
        "arm_session_wall_ns": {
            arm["arm"]: arm["session_wall_ns"] for arm in result["arms"]
        },
        "effect_to_next_ready_ns": {
            arm: {
                "n": len(values),
                "median": statistics.median(values),
                "max": max(values),
            } for arm, values in latencies.items()
        },
        "classification": "PASS_CONSTRUCTION_MECHANICS_ONLY" if not errors and all(corruptions.values())
        else "FAIL_PILOT_AUDIT",
        "scope": "single construction pair on linux/arm64; no formal or x86_64 claim",
    }
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["classification"] == "PASS_CONSTRUCTION_MECHANICS_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())

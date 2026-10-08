#!/usr/bin/env python3
"""Classify operations under the frozen Issue #8609 degradation contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

OPS = {
    "read_raw": ("raw_observer",),
    "inspect_semantic": ("raw_observer", "semantic_observer"),
    "admit_reversible_action": (
        "planner",
        "raw_observer",
        "semantic_observer",
        "verifier",
        "effect_observer",
    ),
    "verify_effect_evidence": ("verifier", "effect_observer"),
}
CLAIMS = {
    "read_raw": "RAW_OBSERVATION",
    "inspect_semantic": "SEMANTIC_OBSERVATION",
    "admit_reversible_action": "ACTION_ADMITTED",
    "verify_effect_evidence": "EFFECT_EVIDENCE_REVIEWABLE",
}


def operation_allowed(name: str, scenario: dict) -> bool:
    services = scenario["available_services"]
    if not all(services.get(service) is True for service in OPS[name]):
        return False
    if scenario["evidence_fresh"] is not True:
        return False
    if name == "admit_reversible_action":
        return (
            scenario["authority_granted"] is True
            and scenario["release_channel_available"] is True
            and not scenario["pending_release_ids"]
        )
    return True


def all_operations_allowed(scenario: dict) -> bool:
    return all(operation_allowed(name, scenario) for name in OPS)


def classify(scenario: dict) -> dict:
    allowed = [name for name in OPS if operation_allowed(name, scenario)]
    all_services = all(scenario["available_services"].values())
    action_allowed = "admit_reversible_action" in allowed
    if action_allowed:
        mode = "FULL_V1" if all_services else "CONTROL_CAPABLE_V1"
    elif any(name != "admit_reversible_action" for name in allowed):
        mode = "READ_ONLY_V1"
    else:
        mode = "NO_SUPPORTED_MODE_V1"

    pending = list(scenario["pending_release_ids"])
    return {
        "scenario_id": scenario["scenario_id"],
        "available_services": dict(scenario["available_services"]),
        "authority_granted": scenario["authority_granted"],
        "release_channel_available": scenario["release_channel_available"],
        "evidence_fresh": scenario["evidence_fresh"],
        "pending_release_ids": pending,
        "unlisted_sources": list(scenario["unlisted_sources"]),
        "mode": mode,
        "admissible_operations": allowed,
        "claim_ceiling_by_operation": {
            name: CLAIMS[name] if name in allowed else "NONE" for name in OPS
        },
        "selected_sources_by_operation": {
            name: list(OPS[name]) for name in allowed
        },
        "release_action_eligible": bool(pending)
        and scenario["release_channel_available"] is True,
    }


def build_result(model: dict) -> dict:
    rows = [classify(scenario) for scenario in model["scenarios"]]
    strict = 0
    for scenario in model["scenarios"]:
        if all_services_ready(scenario) and all_operations_allowed(scenario):
            strict += 1
    readonly_versioned = sum(
        any(name != "admit_reversible_action" for name in row["admissible_operations"])
        for row in rows
    )
    readonly_binary = strict
    return {
        "schema": "semantic-degradation-candidate-v1",
        "allocation_id": "8609-T0-A01-20261009",
        "cases": rows,
        "summary": {
            "case_count": len(rows),
            "versioned_readonly_rows": readonly_versioned,
            "binary_readonly_rows": readonly_binary,
            "additional_readonly_rows": readonly_versioned - readonly_binary,
        },
    }


def all_services_ready(scenario: dict) -> bool:
    return all(scenario["available_services"].values()) and (
        scenario["authority_granted"] is True
        and scenario["release_channel_available"] is True
        and scenario["evidence_fresh"] is True
        and not scenario["pending_release_ids"]
    )


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py MODEL.json FREEZE.json")
    model = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    freeze = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    if freeze.get("allocation_id") != "8609-T0-A01-20261009":
        raise SystemExit("allocation ID mismatch")
    print(json.dumps(build_result(model), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

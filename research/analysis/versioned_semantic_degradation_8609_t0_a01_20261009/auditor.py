#!/usr/bin/env python3
"""Independent raw-only audit for Issue #8609 T0 A01."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

SERVICES = (
    "planner",
    "raw_observer",
    "semantic_observer",
    "verifier",
    "effect_observer",
    "telemetry",
)
SPEC = {
    "read_raw": {"requires": ("raw_observer",), "claim": "RAW_OBSERVATION", "read": True},
    "inspect_semantic": {
        "requires": ("raw_observer", "semantic_observer"),
        "claim": "SEMANTIC_OBSERVATION",
        "read": True,
    },
    "admit_reversible_action": {
        "requires": (
            "planner",
            "raw_observer",
            "semantic_observer",
            "verifier",
            "effect_observer",
        ),
        "claim": "ACTION_ADMITTED",
        "read": False,
    },
    "verify_effect_evidence": {
        "requires": ("verifier", "effect_observer"),
        "claim": "EFFECT_EVIDENCE_REVIEWABLE",
        "read": True,
    },
}
EXPECTED_TOP_KEYS = {"schema", "allocation_id", "cases", "summary"}


def encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_row(scenario: dict) -> dict:
    allowed = []
    for name, contract in SPEC.items():
        if not all(scenario["available_services"].get(s) is True for s in contract["requires"]):
            continue
        if scenario["evidence_fresh"] is not True:
            continue
        if name == "admit_reversible_action":
            if scenario["authority_granted"] is not True:
                continue
            if scenario["release_channel_available"] is not True:
                continue
            if scenario["pending_release_ids"]:
                continue
        allowed.append(name)

    all_services = all(scenario["available_services"].values())
    action_allowed = "admit_reversible_action" in allowed
    if action_allowed:
        mode = "FULL_V1" if all_services else "CONTROL_CAPABLE_V1"
    elif any(SPEC[name]["read"] for name in allowed):
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
            name: SPEC[name]["claim"] if name in allowed else "NONE" for name in SPEC
        },
        "selected_sources_by_operation": {
            name: list(SPEC[name]["requires"]) for name in allowed
        },
        "release_action_eligible": bool(pending)
        and scenario["release_channel_available"] is True,
    }


def audit_rows(model: dict, raw: dict, allocation_id: str) -> list[str]:
    errors = []
    if set(raw) != EXPECTED_TOP_KEYS:
        errors.append("top-level-shape")
    if raw.get("schema") != "semantic-degradation-candidate-v1":
        errors.append("candidate-schema")
    if raw.get("allocation_id") != allocation_id:
        errors.append("allocation-id")
    scenarios = model.get("scenarios", [])
    rows = raw.get("cases", [])
    if len(rows) != len(scenarios):
        errors.append("row-count")
    by_id = {row.get("scenario_id"): row for row in rows}
    if len(by_id) != len(rows):
        errors.append("duplicate-case-id")
    for scenario in scenarios:
        found = by_id.get(scenario["scenario_id"])
        if found is None:
            errors.append("missing-row:" + scenario["scenario_id"])
            continue
        if found != expected_row(scenario):
            errors.append("row-mismatch:" + scenario["scenario_id"])

    # Check every one-bit cover edge of the finite capability lattice. By
    # transitivity, these adjacent checks establish monotonicity for all pairs.
    by_state = {}
    for scenario in scenarios:
        state = state_key(scenario)
        if state in by_state:
            errors.append("duplicate-capability-state")
        by_state[state] = scenario
    dimensions = list(range(len(SERVICES) + 4))
    for state, weaker in by_state.items():
        for dimension in dimensions:
            # Pending release is adverse when true; all other dimensions are
            # capabilities that are stronger when true.
            stronger_bit = 0 if dimension == len(SERVICES) + 3 else 1
            weaker_bit = 1 - stronger_bit
            if state[dimension] != weaker_bit:
                continue
            adjacent = list(state)
            adjacent[dimension] = stronger_bit
            stronger = by_state.get(tuple(adjacent))
            if stronger is None:
                errors.append("missing-lattice-neighbor:" + weaker["scenario_id"])
                continue
            weak_row = by_id.get(weaker["scenario_id"])
            strong_row = by_id.get(stronger["scenario_id"])
            if weak_row is None or strong_row is None:
                continue
            if not set(weak_row.get("admissible_operations", [])).issubset(
                set(strong_row.get("admissible_operations", []))
            ):
                errors.append("nonmonotone-operations:" + weaker["scenario_id"])
            for name in SPEC:
                weak_claim = weak_row.get("claim_ceiling_by_operation", {}).get(name, "NONE")
                strong_claim = strong_row.get("claim_ceiling_by_operation", {}).get(name, "NONE")
                if weak_claim != "NONE" and strong_claim != weak_claim:
                    errors.append("nonmonotone-claim:" + weaker["scenario_id"] + ":" + name)

    read_versioned = sum(
        any(SPEC.get(name, {}).get("read", False) for name in row.get("admissible_operations", []))
        for row in rows
    )
    read_binary = sum(
        all(scenario["available_services"].values())
        and scenario["authority_granted"] is True
        and scenario["release_channel_available"] is True
        and scenario["evidence_fresh"] is True
        and not scenario["pending_release_ids"]
        for scenario in scenarios
    )
    expected_summary = {
        "case_count": len(scenarios),
        "versioned_readonly_rows": read_versioned,
        "binary_readonly_rows": read_binary,
        "additional_readonly_rows": read_versioned - read_binary,
    }
    if raw.get("summary") != expected_summary:
        errors.append("summary-mismatch")
    if read_versioned <= read_binary:
        errors.append("no-additional-readonly-outcomes")
    return errors


def state_key(scenario: dict) -> tuple[bool, ...]:
    return tuple(scenario["available_services"][name] for name in SERVICES) + (
        scenario["authority_granted"],
        scenario["release_channel_available"],
        scenario["evidence_fresh"],
        bool(scenario["pending_release_ids"]),
    )


def verify_hashes(model_path: Path, freeze_path: Path, freeze: dict) -> list[str]:
    errors = []
    if digest_file(model_path) != freeze.get("model_sha256"):
        errors.append("model-hash")
    for name, expected in freeze.get("source_sha256", {}).items():
        if digest_file(Path(name)) != expected:
            errors.append("source-hash:" + name)
    return errors


def mutation_probes(model: dict, raw: dict, allocation_id: str) -> list[bool]:
    probes = []
    eligible = next(r for r in raw["cases"] if r["admissible_operations"])
    row_index = raw["cases"].index(eligible)

    changed = copy.deepcopy(raw)
    changed["cases"][row_index]["selected_sources_by_operation"][
        changed["cases"][row_index]["admissible_operations"][0]
    ] = []
    probes.append(bool(audit_rows(model, changed, allocation_id)))

    stale_model = copy.deepcopy(model)
    stale_scenario = next(s for s in stale_model["scenarios"] if not s["evidence_fresh"])
    changed = copy.deepcopy(raw)
    stale_row = next(r for r in changed["cases"] if r["scenario_id"] == stale_scenario["scenario_id"])
    stale_row["evidence_fresh"] = True
    probes.append(bool(audit_rows(model, changed, allocation_id)))

    no_authority = next(r for r in raw["cases"] if not r["authority_granted"])
    changed = copy.deepcopy(raw)
    changed["cases"][raw["cases"].index(no_authority)]["authority_granted"] = True
    probes.append(bool(audit_rows(model, changed, allocation_id)))

    raw_row = next(r for r in raw["cases"] if "read_raw" in r["admissible_operations"])
    changed = copy.deepcopy(raw)
    changed["cases"][raw["cases"].index(raw_row)]["claim_ceiling_by_operation"]["read_raw"] = "ACTION_ADMITTED"
    probes.append(bool(audit_rows(model, changed, allocation_id)))

    changed = copy.deepcopy(raw)
    changed["cases"][row_index]["selected_sources_by_operation"][
        changed["cases"][row_index]["admissible_operations"][0]
    ].append("private_cache")
    probes.append(bool(audit_rows(model, changed, allocation_id)))

    pending_scenario = next(s for s in model["scenarios"] if s["pending_release_ids"])
    pending_row = next(r for r in raw["cases"] if r["scenario_id"] == pending_scenario["scenario_id"])
    changed = copy.deepcopy(raw)
    changed["cases"][raw["cases"].index(pending_row)]["pending_release_ids"] = []
    probes.append(bool(audit_rows(model, changed, allocation_id)))
    return probes


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        raise SystemExit("usage: auditor.py MODEL.json FREEZE.json CANDIDATE.json")
    model_path, freeze_path, raw_path = map(Path, argv[1:])
    model = json.loads(model_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = verify_hashes(model_path, freeze_path, freeze)
    errors.extend(audit_rows(model, raw, freeze["allocation_id"]))
    probes = mutation_probes(model, raw, freeze["allocation_id"])
    if len(probes) != 6 or not all(probes):
        errors.append("mutation-controls-not-all-rejected")
    result = {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "cases_audited": len(model["scenarios"]),
        "mutation_controls_rejected": sum(probes),
        "mutation_controls_total": len(probes),
        "errors": errors,
        "mutation_results": probes,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

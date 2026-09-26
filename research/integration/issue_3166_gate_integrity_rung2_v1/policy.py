"""Fixture-bound admission comparators for Issue #3166 rung2."""
from __future__ import annotations

POLICIES = (
    "TWO_TIER_FRESH_GATE",
    "DEPENDENCY_ONLY",
    "GATE_ONLY",
    "CACHED_PREPARE_GATE",
)

SCENARIOS = (
    "valid",
    "stale_dependency_version",
    "fresh_false",
    "fresh_unknown",
    "stale_true",
    "lineage_mismatch",
    "missing_lineage",
    "malformed_timestamp",
    "cross_intent",
    "cross_epoch",
)


def dependency_current(prepared: dict, current: dict) -> bool:
    return (
        type(prepared.get("dependency_version")) is int
        and type(current.get("dependency_version")) is int
        and prepared["dependency_version"] == current["dependency_version"]
        and type(prepared.get("observation_generation")) is int
        and type(current.get("observation_generation")) is int
        and prepared["observation_generation"] == current["observation_generation"]
    )


def gate_is_current(prepared: dict, gate: object, now_ns: int) -> bool:
    if type(gate) is not dict:
        return False
    required = {
        "schema", "source_id", "target_id", "lineage", "truth",
        "issued_at_ns", "intent_id", "commit_epoch",
    }
    if set(gate) != required:
        return False
    if gate["schema"] != "fixture-commit-gate-v1":
        return False
    for key in ("source_id", "target_id", "lineage", "intent_id"):
        if type(gate[key]) is not str or not gate[key]:
            return False
    if type(gate["commit_epoch"]) is not int or type(gate["issued_at_ns"]) is not int:
        return False
    if gate["truth"] is not True:
        return False
    if gate["source_id"] != prepared["source_id"]:
        return False
    if gate["target_id"] != prepared["target_id"]:
        return False
    if gate["lineage"] != prepared["lineage"]:
        return False
    if gate["intent_id"] != prepared["intent_id"]:
        return False
    if gate["commit_epoch"] != prepared["commit_epoch"]:
        return False
    prepared_ns = prepared.get("prepared_at_ns")
    if type(prepared_ns) is not int or gate["issued_at_ns"] < prepared_ns:
        return False
    if gate["issued_at_ns"] > now_ns or now_ns - gate["issued_at_ns"] > 15_000_000_000:
        return False
    return True


def admits(policy: str, prepared: dict, current: dict, gate: object, now_ns: int) -> bool:
    dep_ok = dependency_current(prepared, current)
    fresh_gate_ok = gate_is_current(prepared, gate, now_ns)
    if policy == "TWO_TIER_FRESH_GATE":
        return dep_ok and fresh_gate_ok
    if policy == "DEPENDENCY_ONLY":
        return dep_ok
    if policy == "GATE_ONLY":
        return fresh_gate_ok
    if policy == "CACHED_PREPARE_GATE":
        return dep_ok and prepared.get("cached_prepare_gate") is True
    raise ValueError(f"unknown policy: {policy}")


def context(scenario: str, now_ns: int) -> tuple[dict, dict, dict | object]:
    prepared_at = now_ns - 1_000_000
    prepared = {
        "source_id": "gtk-fixture-source-01",
        "target_id": "gtk-window-01",
        "lineage": "x11-display-01/window-generation-01",
        "intent_id": "intent-rung2-01",
        "commit_epoch": 9,
        "dependency_version": 5,
        "observation_generation": 18,
        "prepared_at_ns": prepared_at,
        "cached_prepare_gate": True,
    }
    current = {
        "target_live": True,
        "dependency_version": 5,
        "observation_generation": 18,
    }
    gate = {
        "schema": "fixture-commit-gate-v1",
        "source_id": prepared["source_id"],
        "target_id": prepared["target_id"],
        "lineage": prepared["lineage"],
        "truth": True,
        "issued_at_ns": now_ns,
        "intent_id": prepared["intent_id"],
        "commit_epoch": prepared["commit_epoch"],
    }
    if scenario == "stale_dependency_version":
        current["dependency_version"] = 6
    elif scenario == "fresh_false":
        gate["truth"] = False
    elif scenario == "fresh_unknown":
        gate["truth"] = "UNKNOWN"
    elif scenario == "stale_true":
        gate["issued_at_ns"] = prepared_at - 60_000_000_000
    elif scenario == "lineage_mismatch":
        gate["lineage"] = "x11-display-01/window-generation-00"
    elif scenario == "missing_lineage":
        del gate["lineage"]
    elif scenario == "malformed_timestamp":
        gate["issued_at_ns"] = "not-an-integer"
    elif scenario == "cross_intent":
        gate["intent_id"] = "intent-other"
    elif scenario == "cross_epoch":
        gate["commit_epoch"] = 8
    elif scenario != "valid":
        raise ValueError(f"unknown scenario: {scenario}")
    return prepared, current, gate

#!/usr/bin/env python3
"""One-shot read-only endpoint-eligibility inventory for Issue #6195 T1."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

MAIN_SHA = "14b81dd1f6853623a694266b98538f812847257a"
SOURCES = {
    "v38": {"git_blob": "02d65d49b61feadbdec2e051bd23d1ca845d5df1", "repo_path": "research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl"},
    "v39": {"git_blob": "cbaeed9c7ba27b53cef9d10730ae33313371ad9a", "repo_path": "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"},
}
CONSUMPTION_KEYS = {"consumed_sequence", "consumed_generation", "source_generation", "source_observation_id", "consumed_observation_id"}
DECISION_EVENTS = {"decision", "model_response", "plan", "plan_received", "policy_output", "action_selection"}
EFFECT_EVENTS = {"task_effect", "effect_scored", "independent_effect", "objective_effect"}
EFFECT_KEYS = {"independent_effect_id", "task_effect_score", "independent_scorer", "effect_oracle_id"}
RELEASE_EVENTS = {"input_released", "keys_released", "release_verified"}


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def flatten_keys(value, prefix="") -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            found.add(str(key))
            found.update(flatten_keys(child, name))
    elif isinstance(value, list):
        for child in value:
            found.update(flatten_keys(child, prefix))
    return found


def verified_release(row: dict) -> bool:
    return row.get("event") in RELEASE_EVENTS and any(row.get(k) is True for k in ("verified_empty", "empty_input_verified", "terminal_input_empty")) and any(type(v) is int and k.endswith("_ns") for k, v in row.items())


def explicit_clock(row: dict) -> str | None:
    domain = row.get("clock_domain", row.get("monotonic_clock_id"))
    has_time = any(type(v) is int and k.endswith("_ns") for k, v in row.items())
    return str(domain) if domain is not None and has_time else None


def binding_values(value) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in CONSUMPTION_KEYS and child not in (None, ""):
                found.append(json.dumps(child, sort_keys=True))
            found.extend(binding_values(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(binding_values(child))
    return found


def release_matches(held_row: dict, release_row: dict) -> bool:
    if not verified_release(release_row) or not held_row.get("id") or held_row.get("id") != release_row.get("id"):
        return False
    if "step" in held_row and held_row.get("step") != release_row.get("step"):
        return False
    if "keys" in held_row and "keys" in release_row and held_row.get("keys") != release_row.get("keys"):
        return False
    return True


def inspect(label: str, path: Path) -> dict:
    raw = path.read_bytes()
    expected = SOURCES[label]
    blob = git_blob_sha(raw)
    if blob != expected["git_blob"]:
        raise ValueError(f"{label}: Git blob mismatch {blob}")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    types = Counter(str(row.get("event", "<missing>")) for row in rows)
    captures = [r for r in rows if r.get("event") in {"typed_observation", "observation"} and type(r.get("capture_ns")) is int and type(r.get("sequence")) is int]
    decisions = [r for r in rows if r.get("event") in DECISION_EVENTS and binding_values(r)]
    held = [r for r in rows if r.get("event") == "keys_held"]
    releases = [r for r in rows if r.get("event") in RELEASE_EVENTS]
    verified_releases = [r for r in releases if verified_release(r)]
    available_releases = list(verified_releases)
    matched_release_rows = 0
    for held_row in held:
        match_index = next((i for i, release_row in enumerate(available_releases) if release_matches(held_row, release_row)), None)
        if match_index is not None:
            matched_release_rows += 1
            available_releases.pop(match_index)
    consumed_values = sorted({v for d in decisions for v in binding_values(d)})
    effects = [r for r in rows if r.get("event") in EFFECT_EVENTS or flatten_keys(r) & EFFECT_KEYS]
    fields = sorted(set().union(*(flatten_keys(r) for r in rows))) if rows else []
    domains = {explicit_clock(r) for group in (decisions, held, effects) for r in group}
    gates = {
        "source_capture_with_sequence": bool(captures),
        "decision_bound_to_consumed_generation": bool(decisions),
        "held_input_with_identity_bound_release": bool(held) and matched_release_rows == len(held),
        "same_trace_monotonic_clock_bridges_decision_action_effect": bool(decisions) and bool(held) and bool(effects) and None not in domains and len(domains) == 1,
        "independently_task_relevant_effect": bool(effects),
        "repeated_correction_opportunity": len(consumed_values) >= 2 and bool(held),
    }
    return {
        "label": label,
        "source": expected,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "git_blob_sha": blob,
        "events": len(rows),
        "event_counts": dict(sorted(types.items())),
        "capture_rows": len(captures),
        "generation_bound_decision_rows": len(decisions),
        "distinct_consumed_generation_values": len(consumed_values),
        "keys_held_rows": len(held),
        "release_rows": len(releases),
        "verified_empty_release_rows": len(verified_releases),
        "identity_matched_release_rows": matched_release_rows,
        "effect_rows": len(effects),
        "relevant_field_names": [f for f in fields if any(t in f.lower() for t in ("sequence", "generation", "capture", "effect", "score", "release", "decision", "source", "clock"))],
        "gates": gates,
        "eligible": all(gates.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v38", required=True)
    ap.add_argument("--v39", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    reports = [inspect("v38", Path(args.v38)), inspect("v39", Path(args.v39))]
    eligible = any(r["eligible"] for r in reports)
    result = {
        "schema": "agent-interface/6195-t1-trace-eligibility-v1",
        "allocation_id": "MAP01-DELAY-GAIN-TRACE-ELIGIBILITY-6195-T1-20261001-01",
        "main_sha": MAIN_SHA,
        "traces": reports,
        "disposition": "T1_ELIGIBLE_TRACE_FOUND" if eligible else "HOLD_NO_CLOSED_LOOP_TRACE",
        "scope": "read-only inventory of exactly two retained v38/v39 JSONL traces; missing identity/effect edges are not inferred; no new model, GUI, game, input, or causal claim",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["disposition"], "traces": len(reports), "eligible": sum(r["eligible"] for r in reports)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

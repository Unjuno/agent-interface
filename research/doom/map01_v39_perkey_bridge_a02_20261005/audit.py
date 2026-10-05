#!/usr/bin/env python3
"""Independently audit the retained V4/V12 construction outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE / "results/construction-a02"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path: Path, errors: list[str]):
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(path.name + ":" + type(exc).__name__)
        return []


def main() -> int:
    errors = []
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["source_sha256"].items():
        path = REPO / relative
        if not path.is_file() or sha(path.read_bytes()) != expected:
            errors.append("source_sha256:" + relative)

    event_path = OUT / "candidate-events.jsonl"
    operation_path = OUT / "operation-trace.jsonl"
    result_path = OUT / "candidate.json"
    try:
        event_bytes = event_path.read_bytes()
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append("candidate_artifacts:" + type(exc).__name__)
        event_bytes, result = b"", {}
    events = read_jsonl(event_path, errors)
    operations = read_jsonl(operation_path, errors)

    if result.get("schema") != "map01-v39-v4-v12-composition-candidate-v1":
        errors.append("candidate_schema")
    if result.get("run_id") != freeze.get("run_id"):
        errors.append("run_id")
    if result.get("base_commit") != freeze.get("base_commit"):
        errors.append("base_commit")
    if result.get("status") != "CANDIDATE_EXECUTED":
        errors.append("candidate_status")
    if result.get("environment") != {
        "fake_x_display": True, "os_input": False, "gui_capture": False,
        "vizdoom": False, "model_calls": 0, "docker": False,
    }:
        errors.append("environment_scope")
    if sha(event_bytes) != result.get("candidate", {}).get("events_sha256"):
        errors.append("event_sha256")
    try:
        operation_bytes = operation_path.read_bytes()
    except OSError:
        operation_bytes = b""
    if sha(operation_bytes) != result.get("candidate", {}).get("operation_trace_sha256"):
        errors.append("operation_trace_sha256")
    if len(events) != 4:
        errors.append("expected_four_events")

    admissions = [row for row in events if row.get("event") == "input_admission"]
    releases = [row for row in events if row.get("event") == "input_release_transition"]
    if len(admissions) != 2 or len(releases) != 2:
        errors.append("expected_two_admissions_and_releases")
    else:
        if [row.get("key") for row in admissions] != ["F8", "SPACE"]:
            errors.append("admission_order")
        if [row.get("key") for row in releases] != ["SPACE", "F8"]:
            errors.append("release_order")
        if [row.get("event") for row in events] != [
            "input_admission", "input_admission",
            "input_release_transition", "input_release_transition",
        ]:
            errors.append("event_order")
        admission_by_key = {row.get("key"): row for row in admissions}
        for row in admissions:
            measurement = row.get("physical_key_measurement", {})
            edge = measurement.get("adapter_edge") or {}
            if measurement.get("classification") != "CONFIRMED_PHYSICAL_DOWN":
                errors.append("confirmed_down:" + str(row.get("key")))
            if edge.get("edge") != "down" or edge.get("status") != "CONFIRMED_PHYSICAL_DOWN":
                errors.append("down_adapter_edge:" + str(row.get("key")))
            if (row.get("id"), row.get("step"), row.get("intent_token")) != (
                "cover-v4-a02", 2, "intent-v39-v4-a02"
            ):
                errors.append("down_intent:" + str(row.get("key")))
            if (edge.get("key") != row.get("key")
                    or edge.get("intent_token") != row.get("intent_token")
                    or edge.get("owner_id") != row.get("owner_id")
                    or edge.get("actuation_id") != measurement.get("actuation_id")
                    or measurement.get("identity_status") != "MINTED"
                    or row.get("admission_key_matches_request") is not True):
                errors.append("down_edge_identity:" + str(row.get("key")))
        if set(admission_by_key) != {"F8", "SPACE"}:
            errors.append("admission_key_set")
        for position, row in enumerate(releases):
            measurement = row.get("physical_key_measurement", {})
            edge = measurement.get("adapter_edge") or {}
            interval = edge.get("interval")
            if measurement.get("classification") != "CONFIRMED_PHYSICAL_UP":
                errors.append("confirmed_up:" + str(row.get("key")))
            if edge.get("edge") != "up" or edge.get("status") != "CONFIRMED_PHYSICAL_UP":
                errors.append("up_adapter_edge:" + str(row.get("key")))
            if type(interval) is not list or len(interval) != 2 or any(type(x) is not int for x in interval) or interval[0] > interval[1]:
                errors.append("ordered_up_interval:" + str(row.get("key")))
            if row.get("release_batch_schema") != "input-release-batch-v4":
                errors.append("v4_batch_schema:" + str(row.get("key")))
            if row.get("release_batch_size") != 2 or row.get("release_batch_position") != position:
                errors.append("release_batch_position:" + str(row.get("key")))
            if row.get("owner_transition_verified") is not True:
                errors.append("v4_post_batch_verification:" + str(row.get("key")))
            if row.get("physical_verification_authoritative") is not False or row.get("grants_input_authority") is not False:
                errors.append("release_authority_boundary:" + str(row.get("key")))
            if row.get("id") != "cover-v4-a02" or row.get("step") != 2 or row.get("intent_token") != "intent-v39-v4-a02":
                errors.append("release_context:" + str(row.get("key")))
            admission = admission_by_key.get(row.get("key"), {})
            down_measurement = admission.get("physical_key_measurement", {})
            if (edge.get("key") != row.get("key")
                    or edge.get("intent_token") != row.get("intent_token")
                    or edge.get("owner_id") != row.get("owner_id")
                    or edge.get("actuation_id") != measurement.get("actuation_id")
                    or measurement.get("actuation_id") != down_measurement.get("actuation_id")
                    or measurement.get("identity_status") != "RETIRED"
                    or row.get("admission_identity_status") != "matched"
                    or row.get("admission_position") != admission.get("admission_position")):
                errors.append("release_edge_identity:" + str(row.get("key")))

    if result.get("candidate", {}).get("physical_keys_after") != []:
        errors.append("physical_keys_not_empty")
    if result.get("candidate", {}).get("backend_held_after") != []:
        errors.append("backend_hold_not_empty")

    key_ups = [i for i, row in enumerate(operations)
               if row.get("operation") == "key-up"]
    if len(key_ups) != 2:
        errors.append("expected_two_key_up_operations")
        between = []
    else:
        between = operations[key_ups[0] + 1:key_ups[1]]
    inter_release_samples = sum(row.get("operation") == "keymap-sample" for row in between)
    if inter_release_samples != 2:
        errors.append("inter_release_keymap_sample_count")
    input_edges = [row for row in operations
                   if row.get("operation") in {"key-down", "key-up"}]
    expected_edges = [
        ("key-down", 74), ("key-down", 65), ("key-up", 65), ("key-up", 74)
    ]
    if [(row.get("operation"), row.get("keycode")) for row in input_edges] != expected_edges:
        errors.append("distinct_keycode_edge_order")
    counts = result.get("candidate", {}).get("fake_display_counts", {})
    if counts != {"keymap_queries": 8, "sync_calls": 4, "injected_edges": 4}:
        errors.append("fake_display_operation_counts")

    gap_ns = None
    if len(releases) == 2:
        gap_ns = releases[1].get("release_call_started_ns", -1) - releases[0].get("release_call_returned_ns", -1)
        if type(gap_ns) is not int or gap_ns < 0:
            errors.append("inter_release_call_gap")
        if gap_ns != result.get("candidate", {}).get("inter_release_call_gap_ns"):
            errors.append("inter_release_call_gap_mismatch")

    audit = {
        "schema": "map01-v39-v4-v12-composition-audit-v1",
        "run_id": freeze["run_id"],
        "status": "PASS_COMPOSITION_DIAGNOSTIC" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "event_count": len(events),
        "inter_release_keymap_sample_count": inter_release_samples,
        "inter_release_call_gap_ns": gap_ns,
        "hard_latency_bound_established": False,
        "scope": "fake-display composition only; no production startup or live latency qualification",
    }
    (OUT / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n",
                                     encoding="utf-8")
    print(json.dumps({"status": audit["status"], "errors": errors,
                      "inter_release_keymap_sample_count": inter_release_samples,
                      "inter_release_call_gap_ns": gap_ns}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

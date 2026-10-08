#!/usr/bin/env python3
"""Independent raw-only reconstruction; does not import candidate.py."""

import json
import hashlib
import sys
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def reference_full(case):
    before, after = case["before"], case["after"]
    if set(before) != set(after):
        return "COLLATERAL_CHANGED", sorted(set(before) ^ set(after)), len(before)
    changed = sorted(key for key in before if before[key] != after[key])
    unauthorized = [key for key in changed if key not in case["authorized_changes"]]
    wrong_primary = any(after.get(key) != val for key, val in case["authorized_changes"].items())
    if wrong_primary:
        return "PRIMARY_EFFECT_MISSING", changed, len(before)
    return ("COLLATERAL_CHANGED" if unauthorized else "CLEAN"), changed, len(before)


def reference_qualification(case):
    m = case["metadata"]
    return (
        case["certificate_version"] == 1
        and case["action_id"] == f"fixture-action:{case['case_id']}"
        and hashlib.sha256(canonical(case["events"])).hexdigest() == case["event_manifest_sha256"]
        and case["observed_generation"] == case["source_generation"]
        and m["writer_inventory_complete"]
        and m["dependency_inventory_complete"]
        and m["dependency_provenance_complete"]
        and m["alias_inventory_complete"]
        and not m["alias_edges"]
        and m["callback_inventory_complete"]
        and not m["callbacks"]
        and m["external_writer_inventory_complete"]
        and not m["external_writers"]
        and m["persistence_complete"]
        and bool(m["elided_collateral_predicates"])
    )


def reconstruct(case, policy):
    truth, truth_changed, full_count = reference_full(case)
    before, after = case["before"], case["after"]
    if policy == "FULL_STATE":
        state_bytes = sum(len(canonical([key, before[key], after[key]])) for key in before)
        return truth, truth_changed, {"state_records_examined": full_count,
                                      "state_read_calls": 2 * full_count,
                                      "state_bytes_examined": state_bytes,
                                      "metadata_records_examined": 0,
                                      "metadata_read_calls": 0,
                                      "certificate_bytes_examined": 0,
                                      "fallback": None}
    if policy == "TARGET_ONLY":
        key = next(iter(case["authorized_changes"]))
        expected = case["authorized_changes"][key]
        verdict = "CLEAN" if case["after"].get(key) == expected else "PRIMARY_EFFECT_MISSING"
        size = len(canonical([key, before.get(key), after.get(key)]))
        return verdict, [], {"state_records_examined": 1, "state_read_calls": 2,
                             "state_bytes_examined": size, "metadata_records_examined": 0,
                             "metadata_read_calls": 0, "certificate_bytes_examined": 0,
                             "fallback": None}
    if policy == "STATIC_DIRECT":
        changed = sorted(k for k in set(case["direct_footprint"])
                         if case["before"].get(k) != case["after"].get(k))
        unexpected = any(k not in case["authorized_changes"] for k in changed)
        keys = sorted(set(case["direct_footprint"]))
        size = sum(len(canonical([k, before.get(k), after.get(k)])) for k in keys)
        return ("COLLATERAL_CHANGED" if unexpected else "CLEAN"), changed, {
            "state_records_examined": len(keys), "state_read_calls": 2 * len(keys),
            "state_bytes_examined": size, "metadata_records_examined": 0,
            "metadata_read_calls": 0, "certificate_bytes_examined": 0, "fallback": None}

    certificate_bytes = len(canonical(case["metadata"])) + len(canonical({
        "certificate_version": case["certificate_version"],
        "action_id": case["action_id"],
        "source_generation": case["source_generation"],
        "observed_generation": case["observed_generation"],
        "direct_footprint": case["direct_footprint"],
        "authorized_changes": case["authorized_changes"],
        "elided_collateral_predicates": case["metadata"]["elided_collateral_predicates"],
    })) + len(canonical(case["events"])) + len(canonical(case["event_manifest_sha256"]))
    if not reference_qualification(case):
        state_bytes = sum(len(canonical([key, before[key], after[key]])) for key in before)
        metadata_count = len(case["metadata"].get("dependency_edges", [])) + \
            len(case["metadata"].get("alias_edges", [])) + len(case["events"]) + 7
        return truth, truth_changed, {
            "state_records_examined": full_count, "state_read_calls": 2 * full_count,
            "state_bytes_examined": state_bytes, "metadata_records_examined": metadata_count,
            "metadata_read_calls": metadata_count, "certificate_bytes_examined": certificate_bytes,
            "fallback": "FULL_STATE"}
    graph = {}
    for source, target, *_provenance in case["metadata"]["dependency_edges"]:
        graph.setdefault(source, set()).add(target)
    footprint = set(case["direct_footprint"])
    frontier = list(footprint)
    while frontier:
        for target in graph.get(frontier.pop(), ()):
            if target not in footprint:
                footprint.add(target)
                frontier.append(target)
    ordered = sorted(footprint)
    changed = [key for key in ordered if case["before"].get(key) != case["after"].get(key)]
    unexpected = any(key not in case["authorized_changes"] for key in changed)
    verdict = "COLLATERAL_CHANGED" if unexpected else "CLEAN"
    state_bytes = sum(len(canonical([key, before.get(key), after.get(key)])) for key in ordered)
    metadata_count = 7 + sum(len(targets) for targets in graph.values()) + len(case["events"])
    return verdict, changed, {
        "state_records_examined": len(ordered), "state_read_calls": 2 * len(ordered),
        "state_bytes_examined": state_bytes, "metadata_records_examined": metadata_count,
        "metadata_read_calls": metadata_count, "certificate_bytes_examined": certificate_bytes,
        "fallback": None}


def audit(inputs, candidate):
    expected = {(case["case_id"], p) for case in inputs["cases"]
                for p in ("TARGET_ONLY", "FULL_STATE", "STATIC_DIRECT", "QUALIFIED_FRAME")}
    got = {(row["case_id"], row["policy"]) for row in candidate["rows"]}
    errors = []
    if len(got) != len(candidate["rows"]):
        errors.append("duplicate_case_policy_row")
    if got != expected:
        errors.append("row_set_mismatch")
    index = {(r["case_id"], r["policy"]): r for r in candidate["rows"]}
    reconstructed = 0
    unsafe_partial_clean = []
    for case in inputs["cases"]:
        truth, _, _ = reference_full(case)
        before, after = case["before"], case["after"]
        state_changes = {key: after[key] for key in after
                         if key not in before or before[key] != after[key]}
        event_writes = {event["key"]: event["new_value"] for event in case["events"]
                        if event.get("kind") == "write"}
        state_changes_explained = all(event_writes.get(key) == value
                                      for key, value in state_changes.items())
        event_values_match_snapshot = all(key in after and after[key] == value
                                          for key, value in event_writes.items())
        if not state_changes_explained or not event_values_match_snapshot:
            errors.append(f"event_state_mismatch:{case['case_id']}")
        if hashlib.sha256(canonical(case["events"])).hexdigest() != case["event_manifest_sha256"]:
            errors.append(f"event_manifest_hash_mismatch:{case['case_id']}")
        admission = [event for event in case["events"] if event.get("kind") == "action_admitted"]
        if len(admission) != 1 or admission[0].get("action_id") != case["action_id"] \
                or admission[0].get("generation") != case["source_generation"]:
            errors.append(f"action_event_binding_mismatch:{case['case_id']}")
        snapshots = [event for event in case["events"] if event.get("kind") == "snapshot_observed"]
        if len(snapshots) != 1 or snapshots[0].get("generation") != case["observed_generation"] \
                or snapshots[0].get("durable") != case["metadata"]["persistence_complete"]:
            errors.append(f"snapshot_event_binding_mismatch:{case['case_id']}")
        for policy in ("TARGET_ONLY", "FULL_STATE", "STATIC_DIRECT", "QUALIFIED_FRAME"):
            key = (case["case_id"], policy)
            row = index.get(key)
            if row is None:
                continue
            verdict, changed, counts = reconstruct(case, policy)
            reconstructed += 1
            if row.get("verdict") != verdict or row.get("changed_keys_observed") != changed:
                errors.append(f"candidate_mismatch:{case['case_id']}:{policy}")
            if row.get("metrics", {}).get("state_records_examined") != counts["state_records_examined"]:
                errors.append(f"state_count_mismatch:{case['case_id']}:{policy}")
            metrics = row.get("metrics", {})
            for name in ("state_read_calls", "state_bytes_examined", "metadata_records_examined",
                         "metadata_read_calls", "certificate_bytes_examined", "fallback"):
                if metrics.get(name) != counts.get(name):
                    errors.append(f"{name}_mismatch:{case['case_id']}:{policy}")
            expected_total = counts["state_bytes_examined"] + counts["certificate_bytes_examined"]
            if metrics.get("accounted_bytes") != expected_total:
                errors.append(f"accounted_bytes_mismatch:{case['case_id']}:{policy}")
            if policy == "QUALIFIED_FRAME" and row.get("verdict") == "CLEAN" and truth != "CLEAN":
                unsafe_partial_clean.append(case["case_id"])
            if policy == "QUALIFIED_FRAME" and reference_qualification(case) and verdict != truth:
                errors.append(f"qualified_frame_full_oracle_parity:{case['case_id']}")
            if policy == "QUALIFIED_FRAME":
                m = case["metadata"]
                expected_gates = {
                    "certificate_version_supported": case["certificate_version"] == 1,
                    "action_identity_bound": case["action_id"] == f"fixture-action:{case['case_id']}",
                    "event_manifest_bound": hashlib.sha256(canonical(case["events"])).hexdigest()
                    == case["event_manifest_sha256"],
                    "event_manifest_bound": hashlib.sha256(canonical(case["events"])).hexdigest()
                    == case["event_manifest_sha256"],
                    "generation_current": case["observed_generation"] == case["source_generation"],
                    "writer_inventory_complete": m["writer_inventory_complete"],
                    "dependency_inventory_complete": m["dependency_inventory_complete"],
                    "dependency_provenance_complete": m["dependency_provenance_complete"],
                    "alias_inventory_complete": m["alias_inventory_complete"] and not m["alias_edges"],
                    "callback_inventory_complete": m["callback_inventory_complete"] and not m["callbacks"],
                    "external_writer_inventory_complete": m["external_writer_inventory_complete"],
                    "no_external_writers": not m["external_writers"],
                    "durable_snapshot": m["persistence_complete"],
                    "collateral_predicates_bound": bool(m["elided_collateral_predicates"]),
                }
                if metrics.get("qualification_gates") != expected_gates:
                    errors.append(f"qualification_gate_mismatch:{case['case_id']}")
                expected_footprint = []
                if all(expected_gates.values()):
                    graph = {}
                    for source, target, *_provenance in m["dependency_edges"]:
                        graph.setdefault(source, set()).add(target)
                    footprint = set(case["direct_footprint"])
                    frontier = list(footprint)
                    while frontier:
                        for target in graph.get(frontier.pop(), ()):
                            if target not in footprint:
                                footprint.add(target)
                                frontier.append(target)
                    expected_footprint = sorted(footprint)
                if metrics.get("qualified_footprint") != expected_footprint:
                    errors.append(f"qualified_footprint_mismatch:{case['case_id']}")
            if policy == "QUALIFIED_FRAME" and row.get("wall_time_median_ns_31", 0) <= 0:
                errors.append(f"missing_timing:{case['case_id']}")

    disjoint_ids = ("genuinely_disjoint_small", "genuinely_disjoint_medium",
                    "genuinely_disjoint_large")
    full_by_case = {case_id: index.get((case_id, "FULL_STATE"), {}).get("metrics", {}).get("accounted_bytes")
                    for case_id in disjoint_ids}
    frame_by_case = {case_id: index.get((case_id, "QUALIFIED_FRAME"), {}).get("metrics", {}).get("accounted_bytes")
                     for case_id in disjoint_ids}
    if any(value is None for value in (*full_by_case.values(), *frame_by_case.values())):
        errors.append("missing_disjoint_cost_rows")
        reduction = None
    else:
        full_total = sum(full_by_case.values())
        frame_total = sum(frame_by_case.values())
        reduction = (full_total - frame_total) / full_total if full_total else None
    return {
        "schema": "issue6533-audit-v1",
        "status": ("FAIL_METHOD" if errors or unsafe_partial_clean else
                   "PASS_METHOD_SCOPED" if reduction is not None and reduction >= 0.10 else
                   "FAIL_NO_COST_REDUCTION"),
        "rows_expected": len(expected), "rows_reconstructed": reconstructed,
        "errors": errors, "unsafe_qualified_frame_clean_cases": unsafe_partial_clean,
        "eligible_disjoint_full_accounted_bytes_by_case": full_by_case,
        "eligible_disjoint_frame_accounted_bytes_by_case": frame_by_case,
        "eligible_disjoint_full_accounted_bytes_total": None if reduction is None else sum(full_by_case.values()),
        "eligible_disjoint_frame_accounted_bytes_total": None if reduction is None else sum(frame_by_case.values()),
        "eligible_disjoint_accounted_byte_reduction_fraction": reduction,
        "cost_gate": "PASS" if reduction is not None and reduction >= 0.10 else "FAIL_NO_COST_REDUCTION",
        "scope": "finite synthetic structured-state method fixture only; no real GUI or production claim",
    }


if __name__ == "__main__":
    input_path, candidate_path, output_path = map(Path, sys.argv[1:4])
    result = audit(json.loads(input_path.read_text()), json.loads(candidate_path.read_text()))
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(f"auditor status={result['status']} rows={result['rows_reconstructed']} errors={len(result['errors'])}")
    if result["status"] != "PASS_METHOD_SCOPED" or result["cost_gate"] != "PASS":
        sys.exit(1)

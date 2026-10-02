#!/usr/bin/env python3
"""One-shot candidate: compare four collateral-check policies on frozen raw cases."""

import json
import hashlib
import statistics
import sys
import time
from pathlib import Path

POLICIES = ("TARGET_ONLY", "FULL_STATE", "STATIC_DIRECT", "QUALIFIED_FRAME")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def full_state(case):
    before, after = case["before"], case["after"]
    changed = [key for key in sorted(before) if before[key] != after[key]]
    collateral = [key for key in changed if key not in case["authorized_changes"]]
    bytes_examined = sum(len(encode([key, before[key], after[key]])) for key in before)
    return ("COLLATERAL_CHANGED" if collateral else "CLEAN", changed,
            {"state_records_examined": len(before), "state_read_calls": 2 * len(before),
             "state_bytes_examined": bytes_examined,
             "metadata_records_examined": 0, "fallback": None})


def target_only(case):
    key, expected = next(iter(case["authorized_changes"].items()))
    actual = case["after"].get(key)
    verdict = "CLEAN" if actual == expected else "PRIMARY_EFFECT_MISSING"
    size = len(encode([key, case["before"].get(key), actual]))
    return verdict, [], {"state_records_examined": 1, "state_read_calls": 2,
                         "state_bytes_examined": size,
                         "metadata_records_examined": 0, "fallback": None}


def static_direct(case):
    keys = sorted(set(case["direct_footprint"]))
    changed = [key for key in keys if case["before"].get(key) != case["after"].get(key)]
    collateral = [key for key in changed if key not in case["authorized_changes"]]
    size = sum(len(encode([key, case["before"].get(key), case["after"].get(key)])) for key in keys)
    return ("COLLATERAL_CHANGED" if collateral else "CLEAN", changed,
            {"state_records_examined": len(keys), "state_read_calls": 2 * len(keys),
             "state_bytes_examined": size,
             "metadata_records_examined": 0, "fallback": None})


def frame_qualifies(case):
    m = case["metadata"]
    gates = {
        "certificate_version_supported": case["certificate_version"] == 1,
        "action_identity_bound": case["action_id"] == f"fixture-action:{case['case_id']}",
        "event_manifest_bound": hashlib.sha256(encode(case["events"])).hexdigest()
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
    return all(gates.values()), gates


def transitive_footprint(case):
    graph = {}
    for source, target, *_provenance in case["metadata"]["dependency_edges"]:
        graph.setdefault(source, set()).add(target)
    seen = set(case["direct_footprint"])
    frontier = list(seen)
    while frontier:
        source = frontier.pop()
        for target in graph.get(source, ()):
            if target not in seen:
                seen.add(target)
                frontier.append(target)
    return sorted(seen), sum(1 for edges in graph.values() for _ in edges)


def qualified_frame(case):
    cert_bytes = len(encode(case["metadata"])) + len(encode({
        "certificate_version": case["certificate_version"],
        "action_id": case["action_id"],
        "source_generation": case["source_generation"],
        "observed_generation": case["observed_generation"],
        "direct_footprint": case["direct_footprint"],
        "authorized_changes": case["authorized_changes"],
        "elided_collateral_predicates": case["metadata"]["elided_collateral_predicates"],
    })) + len(encode(case["events"])) + len(encode(case["event_manifest_sha256"]))
    qualifies, gates = frame_qualifies(case)
    if not qualifies:
        verdict, changed, metrics = full_state(case)
        metrics.update({"metadata_records_examined": len(case["metadata"].get("dependency_edges", []))
                        + len(case["metadata"].get("alias_edges", [])) + len(case["events"]) + 7,
                        "certificate_bytes_examined": cert_bytes,
                        "fallback": "FULL_STATE"})
        metrics["state_read_calls"] = 2 * metrics["state_records_examined"]
        metrics["metadata_read_calls"] = metrics["metadata_records_examined"]
        return verdict, changed, metrics, gates, []

    footprint, edge_count = transitive_footprint(case)
    changed = [key for key in footprint if case["before"].get(key) != case["after"].get(key)]
    collateral = [key for key in changed if key not in case["authorized_changes"]]
    state_bytes = sum(len(encode([key, case["before"].get(key), case["after"].get(key)]))
                      for key in footprint)
    metrics = {
        "state_records_examined": len(footprint),
        "state_read_calls": 2 * len(footprint),
        "state_bytes_examined": state_bytes,
        "metadata_records_examined": 7 + edge_count + len(case["events"]),
        "metadata_read_calls": 7 + edge_count + len(case["events"]),
        "certificate_bytes_examined": cert_bytes,
        "fallback": None,
    }
    return ("COLLATERAL_CHANGED" if collateral else "CLEAN", changed, metrics, gates, footprint)


def evaluate(case, policy):
    if policy == "TARGET_ONLY":
        verdict, changed, metrics = target_only(case)
    elif policy == "FULL_STATE":
        verdict, changed, metrics = full_state(case)
    elif policy == "STATIC_DIRECT":
        verdict, changed, metrics = static_direct(case)
    else:
        verdict, changed, metrics, gates, footprint = qualified_frame(case)
        metrics["qualification_gates"] = gates
        metrics["qualified_footprint"] = footprint
        metrics["certificate_bytes_examined"] = metrics.get("certificate_bytes_examined", 0)
    if policy != "QUALIFIED_FRAME":
        metrics["certificate_bytes_examined"] = 0
        metrics["metadata_read_calls"] = 0
    metrics["accounted_bytes"] = metrics["state_bytes_examined"] + metrics["certificate_bytes_examined"]
    return verdict, changed, metrics


def measured_median_ns(case, policy, repeats=31):
    samples = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        evaluate(case, policy)
        samples.append(time.perf_counter_ns() - start)
    return int(statistics.median(samples))


def run(inputs):
    rows = []
    for case in inputs["cases"]:
        for policy in POLICIES:
            verdict, changed, metrics = evaluate(case, policy)
            rows.append({"case_id": case["case_id"], "policy": policy, "verdict": verdict,
                         "changed_keys_observed": changed, "metrics": metrics,
                         "wall_time_median_ns_31": measured_median_ns(case, policy)})
    return {"schema": "issue6533-candidate-v1", "rows": rows}


if __name__ == "__main__":
    input_path, output_path = map(Path, sys.argv[1:3])
    output_path.write_text(json.dumps(run(json.loads(input_path.read_text())),
                                      sort_keys=True, indent=2) + "\n")
    print(f"candidate emitted {len(json.loads(output_path.read_text())['rows'])} rows")

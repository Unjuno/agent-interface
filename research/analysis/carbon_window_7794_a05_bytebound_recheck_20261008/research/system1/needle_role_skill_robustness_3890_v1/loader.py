"""Independent data-only artifact validator/loader; no dynamic code or torch.load."""
import argparse
import gzip
import hashlib
import json
import math
import os
import sys

import torch

ALLOCATION = "needle-role-skill-robustness-3890-v1"
ISSUE_CONTRACT_SHA256 = "872022a1f2eec0b83f48f3704e2c3df7eedeeaaba9deb5128f74f3f4880cc691"
SCHEMA = "unjuno.role-skill.numeric-json.v1"
EXPECTED_KEYS = {
    "A": {"enc.0.weight", "enc.0.bias", "head.weight", "head.bias"},
    "B": {"core.enc.0.weight", "core.enc.0.bias", "core.head.weight",
          "core.head.bias", "a", "b"},
    "C": {"core.enc.0.weight", "core.enc.0.bias", "core.head.weight",
          "core.head.bias", "a", "b"},
}
SHAPES = {"enc.0.weight": [16, 8], "enc.0.bias": [16],
          "head.weight": [4, 16], "head.bias": [4],
          "core.enc.0.weight": [16, 8], "core.enc.0.bias": [16],
          "core.head.weight": [4, 16], "core.head.bias": [4],
          "a": [16, 2], "b": [2, 4]}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def hash_payload(value):
    unsigned = {key: item for key, item in value.items() if key != "payload_sha256"}
    return hashlib.sha256(canonical(unsigned)).hexdigest()


def no_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def nested_shape(value):
    if not isinstance(value, list):
        return []
    return [len(value), *nested_shape(value[0])] if value else [0]


def valid_numbers(value):
    if isinstance(value, list):
        return all(valid_numbers(item) for item in value)
    return type(value) in (int, float) and math.isfinite(value) and abs(value) < 1e6


def validate(artifact_path, expected_seed):
    raw = open(artifact_path, "rb").read()
    if len(raw) > 4_000_000:
        raise ValueError("package_too_large")
    obj = json.loads(raw, object_pairs_hook=no_duplicate_pairs)
    if set(obj) != {"schema", "generation", "architecture", "graph",
                    "provenance", "tensors", "payload_sha256"}:
        raise ValueError("schema_keys")
    if obj["schema"] != SCHEMA:
        raise ValueError("schema")
    if obj["generation"] != expected_seed:
        raise ValueError("generation")
    if obj["architecture"] != {"input": 8, "hidden": 16, "classes": 4,
                               "rank": 2, "roles": ["A", "B", "C"]}:
        raise ValueError("architecture")
    graph = {"nodes": [{"id": r, "version": r + "-v1"} for r in ("A", "B", "C")],
             "edges": [["A", "B"], ["B", "C"]], "scope": "synthetic-fixture-v1"}
    if obj["graph"] != graph:
        raise ValueError("graph_manifest")
    provenance = {"allocation": ALLOCATION, "issue": 4479,
                  "issue_contract_sha256": ISSUE_CONTRACT_SHA256,
                  "predecessor_issue": 3890, "seed": expected_seed,
                  "family": "synthetic-role-adapter-v1"}
    if obj["provenance"] != provenance:
        raise ValueError("provenance")
    claimed = obj.pop("payload_sha256")
    if hashlib.sha256(canonical(obj)).hexdigest() != claimed:
        raise ValueError("payload_digest")
    if set(obj["tensors"]) != {"A", "B", "C"}:
        raise ValueError("roles")
    for role, state in obj["tensors"].items():
        if set(state) != EXPECTED_KEYS[role]:
            raise ValueError("tensor_keys")
        for name, values in state.items():
            if nested_shape(values) != SHAPES[name] or not valid_numbers(values):
                raise ValueError("tensor_shape_or_value")
    obj["payload_sha256"] = claimed
    return obj, hashlib.sha256(raw).hexdigest()


def infer(artifact, role, rows):
    state = artifact["tensors"][role]
    tensor = lambda key: torch.tensor(state[key], dtype=torch.float32)
    x = torch.tensor(rows, dtype=torch.float32)
    if role == "A":
        h = torch.tanh(torch.nn.functional.linear(x, tensor("enc.0.weight"),
                                                  tensor("enc.0.bias")))
        logits = torch.nn.functional.linear(h, tensor("head.weight"), tensor("head.bias"))
    else:
        h = torch.tanh(torch.nn.functional.linear(x, tensor("core.enc.0.weight"),
                                                  tensor("core.enc.0.bias")))
        logits = torch.nn.functional.linear(h, tensor("core.head.weight"),
                                            tensor("core.head.bias")) + h @ tensor("a") @ tensor("b") / 2
    return logits.argmax(-1).tolist()


def step(graph, source, target, generation, receipt_id, version,
         verified=True, scope="synthetic-fixture-v1"):
    edges = {"A": ["B"], "B": ["C"], "C": []}
    cursor = graph["cursor"]
    ok = (source == cursor and target in edges[cursor] and generation == graph["generation"]
          and receipt_id not in graph["accepted"] and version == source + "-v1"
          and verified is True and scope == "synthetic-fixture-v1")
    if not ok:
        return "YIELD"
    graph["accepted"].add(receipt_id)
    graph["cursor"] = target
    graph["emissions"] += 1
    return "ADVANCE"


def graph_state(graph):
    return graph["cursor"], graph["generation"], tuple(sorted(graph["accepted"])), graph["emissions"]


def exercise(generation):
    graph = {"generation": generation, "cursor": "A", "accepted": set(), "emissions": 0}
    controls = {}
    bad = [
        ("wrong_adapter_version", ("A", "B", generation, "ver", "A-v0", True, "synthetic-fixture-v1")),
        ("skipped_edge", ("A", "C", generation, "skip", "A-v1", True, "synthetic-fixture-v1")),
        ("wrong_scope", ("A", "B", generation, "scope", "A-v1", True, "other")),
        ("unverified_outcome", ("A", "B", generation, "unverified", "A-v1", False, "synthetic-fixture-v1")),
        ("unknown_destination", ("A", "Z", generation, "unknown", "A-v1", True, "synthetic-fixture-v1")),
        ("stale_generation", ("A", "B", generation - 100, "stale", "A-v1", True, "synthetic-fixture-v1")),
    ]
    initial = graph_state(graph)
    for name, args in bad:
        before = graph_state(graph)
        controls[name] = step(graph, *args)
        if graph_state(graph) != before:
            raise ValueError("refusal_mutated_graph:" + name)
    controls["duplicate_receipt"] = step(graph, "A", "B", generation, "dup", "A-v1")
    accepted_state = graph_state(graph)
    controls["duplicate_receipt_replay"] = step(graph, "B", "C", generation, "dup", "B-v1")
    if graph_state(graph) != accepted_state:
        raise ValueError("duplicate_receipt_mutated_graph")
    graph = {"generation": generation, "cursor": "A", "accepted": set(), "emissions": 0}
    flow = [step(graph, "A", "B", generation, "a-" + str(generation), "A-v1"),
            step(graph, "B", "C", generation, "b-" + str(generation), "B-v1")]
    return {"generation": generation, "controls": controls, "flow": flow,
            "cursor": graph["cursor"], "fixture_emissions": graph["emissions"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact")
    parser.add_argument("expected")
    parser.add_argument("out")
    args = parser.parse_args()
    try:
        with gzip.open(args.expected, "rt", encoding="utf-8") as f:
            expected = json.load(f, object_pairs_hook=no_duplicate_pairs)
        seed = expected["seed"]
        package_before = hashlib.sha256(open(args.artifact, "rb").read()).hexdigest()
        artifact, artifact_sha = validate(args.artifact, seed)
        preds = {role: infer(artifact, role, expected["roles"][role]["inputs"])
                 for role in ("A", "B", "C")}
        graphs = [exercise(generation) for generation in (seed, seed + 100)]
        package_after = hashlib.sha256(open(args.artifact, "rb").read()).hexdigest()
        if package_before != package_after or package_before != artifact_sha:
            raise ValueError("package_changed_during_load")
        result = {"accepted": True, "artifact_sha256": artifact_sha,
                  "payload_sha256": artifact["payload_sha256"],
                  "package_sha256_before": package_before,
                  "package_sha256_after": package_after,
                  "predictions": preds, "graphs": graphs}
    except Exception as exc:
        result = {"accepted": False, "error": repr(exc), "type": type(exc).__name__}
    with open(args.out, "x", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"), allow_nan=False)
    print(json.dumps({k: result[k] for k in ("accepted", "artifact_sha256")
                      if k in result}, sort_keys=True))
    return 0 if result["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

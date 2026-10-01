import hashlib
import json
from pathlib import Path


OUT = Path("/out/formal02")
OUT.mkdir(parents=True, exist_ok=False)

PREDICATES = ("semantic", "authority", "lineage", "freshness", "release", "contradiction")


def make_case(case_id, noise=0, stale=False, verifier_skipped=False, unknown_external=False):
    nodes = {}
    for name in PREDICATES:
        nodes[name] = {"value": True, "edges": []}
    nodes["decision"] = {"value": "PASS", "edges": [
        {"to": "semantic", "kind": "data"},
        {"to": "authority", "kind": "data"},
        {"to": "lineage", "kind": "data"},
        {"to": "freshness", "kind": "invalidation"},
        {"to": "release", "kind": "data"},
        {"to": "contradiction", "kind": "control"},
    ]}
    if stale:
        nodes["freshness"]["value"] = False
    if verifier_skipped:
        nodes["contradiction"]["value"] = False
        nodes["verifier_branch"] = {"value": "SKIPPED", "edges": []}
        nodes["decision"]["edges"].append({"to": "verifier_branch", "kind": "control"})
    if unknown_external:
        nodes["decision"]["edges"].append({"to": "external_cause", "kind": "unknown"})
    for i in range(noise):
        nodes[f"noise_{i:03d}"] = {"value": f"irrelevant-{i}", "edges": []}
    return {"case_id": case_id, "graph_complete": not unknown_external,
            "ground_truth": {"semantic": True, "authority": True, "lineage": True,
                             "freshness": not stale, "release": True,
                             "contradiction": not verifier_skipped,
                             "unknown_external": unknown_external},
            "nodes": nodes}


def closure(case, allowed_kinds=None):
    seen, todo = set(), ["decision"]
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        for edge in case["nodes"].get(name, {}).get("edges", []):
            if allowed_kinds is None or edge["kind"] in allowed_kinds:
                todo.append(edge["to"])
    return sorted(seen)


def decide(case, retained, policy):
    if policy == "LABEL_ONLY":
        return case["nodes"]["decision"]["value"]
    if not case["graph_complete"]:
        return "UNKNOWN"
    if any(name not in retained for name in PREDICATES):
        return "UNKNOWN"
    values = {name: case["nodes"][name]["value"] for name in PREDICATES}
    if values["freshness"] is not True:
        return "STALE"
    if values["authority"] is not True:
        return "NO_AUTHORITY"
    if values["lineage"] is not True:
        return "UNATTRIBUTED"
    if values["release"] is not True:
        return "UNRELEASED"
    if values["contradiction"] is not True:
        return "CONTRADICTED_OR_UNCHECKED"
    if values["semantic"] is not True:
        return "NO_EFFECT"
    return "PASS"


def oracle(case):
    gt = case["ground_truth"]
    if gt["unknown_external"]:
        return "UNKNOWN"
    if not gt["freshness"]:
        return "STALE"
    if not gt["authority"]:
        return "NO_AUTHORITY"
    if not gt["lineage"]:
        return "UNATTRIBUTED"
    if not gt["release"]:
        return "UNRELEASED"
    if not gt["contradiction"]:
        return "CONTRADICTED_OR_UNCHECKED"
    if not gt["semantic"]:
        return "NO_EFFECT"
    return "PASS"


cases = [
    make_case("clean_noise_12", noise=12),
    make_case("stale_generation", noise=4, stale=True),
    make_case("verifier_skipped_control", noise=3, verifier_skipped=True),
    make_case("unknown_external_cause", noise=2, unknown_external=True),
]
rows = []
for case in cases:
    raw_nodes = sorted(case["nodes"])
    full = raw_nodes
    label = ["decision"]
    data = closure(case, {"data"})
    typed = closure(case)
    expected = oracle(case)
    rows.append({
        "case_id": case["case_id"], "oracle": expected,
        "full": {"retained": full, "decision": decide(case, full, "RAW_TRACE")},
        "label_only": {"retained": label, "decision": decide(case, label, "LABEL_ONLY")},
        "data_slice": {"retained": data, "decision": decide(case, data, "DATA_SLICE")},
        "typed_slice": {"retained": typed, "decision": decide(case, typed, "TYPED_SLICE")},
        "graph_complete": case["graph_complete"], "ground_truth": case["ground_truth"],
        "nodes": case["nodes"],
    })
payload = {"schema": "issue5329-backward-slice-raw-v1", "allocation": "5329-backward-slice-t0-20261001-02",
           "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "rows": rows}
raw = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
(OUT / "raw.json").write_text(raw, encoding="utf-8")
print(json.dumps({"allocation": payload["allocation"], "rows": len(rows),
                  "raw_sha256": hashlib.sha256(raw.encode()).hexdigest()}, sort_keys=True))

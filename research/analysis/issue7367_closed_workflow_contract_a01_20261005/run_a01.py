import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / "research/analysis/issue7367_context_liveness_a01_20261004"
sys.path.insert(0, str(SOURCE))
import run_a01 as liveness


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compile_source(source, records):
    if not isinstance(source, dict) or set(source) != {"schema", "entry", "nodes"}:
        return {"status": "UNKNOWN_KEEP", "reason": "invalid_top_level_schema"}
    if source["schema"] != "issue7367-closed-workflow-v1" or not isinstance(source["nodes"], dict):
        return {"status": "UNKNOWN_KEEP", "reason": "unsupported_schema"}
    if source["entry"] not in source["nodes"]:
        return {"status": "UNKNOWN_KEEP", "reason": "unknown_entry"}
    by_id = {r.get("id"): r for r in records}
    nodes, edges = {}, {}
    for name, node in source["nodes"].items():
        if not isinstance(name, str) or not isinstance(node, dict) or set(node) != {"uses", "next"}:
            return {"status": "UNKNOWN_KEEP", "reason": "unsupported_node_or_dynamic_operation"}
        if not isinstance(node["uses"], list) or not isinstance(node["next"], list):
            return {"status": "UNKNOWN_KEEP", "reason": "invalid_use_or_edge_list"}
        uses = []
        for pair in node["uses"]:
            if not isinstance(pair, list) or len(pair) != 2:
                return {"status": "UNKNOWN_KEEP", "reason": "invalid_use"}
            ident, field = pair
            if (not isinstance(ident, str) or not isinstance(field, str)
                    or ident not in by_id or field not in by_id[ident].get("fields", {})):
                return {"status": "UNKNOWN_KEEP", "reason": "unresolved_use"}
            uses.append([ident, field])
        if len({tuple(use) for use in uses}) != len(uses):
            return {"status": "UNKNOWN_KEEP", "reason": "duplicate_use"}
        nodes[name] = {"uses": uses}
        edges[name] = list(node["next"])
    for targets in edges.values():
        if any(not isinstance(target, str) or target not in nodes for target in targets):
            return {"status": "UNKNOWN_KEEP", "reason": "unknown_successor"}
        if len(set(targets)) != len(targets):
            return {"status": "UNKNOWN_KEEP", "reason": "duplicate_successor"}
    graph = {"nodes": nodes, "edges": edges}
    return {
        "status": "CLOSED",
        "entry": source["entry"],
        "graph": graph,
        "manifest_sha256": digest(source),
        "graph_sha256": digest(graph),
    }


def evaluate(source, records, expected_manifest_sha=None):
    compiled = compile_source(source, records)
    if compiled["status"] != "CLOSED":
        return {"disposition": "UNKNOWN_KEEP", "selected_ids": [r["id"] for r in records], "evicted_ids": [], "reason": compiled["reason"]}
    if expected_manifest_sha is not None and compiled["manifest_sha256"] != expected_manifest_sha:
        return {"disposition": "UNKNOWN_KEEP", "selected_ids": [r["id"] for r in records], "evicted_ids": [], "reason": "manifest_changed_after_compile"}
    graph = compiled["graph"]
    frozen = {"graph_sha256": compiled["graph_sha256"]}
    work = {"frontier": compiled["entry"], "records": records}
    result = liveness.analyze(work, frozen, graph=graph, scope={"graph_complete": True, "dynamic_consumers_possible": False})
    result["manifest_sha256"] = compiled["manifest_sha256"]
    return result


def execute_node(source, name, records):
    """The closed interpreter exposes only manifest-declared fields."""
    compiled = compile_source(source, records)
    if compiled["status"] != "CLOSED" or name not in compiled["graph"]["nodes"]:
        return {"status": "UNKNOWN_KEEP", "fields": {}}
    by_id = {r["id"]: r for r in records}
    fields = {}
    for ident, field in compiled["graph"]["nodes"][name]["uses"]:
        fields.setdefault(ident, {})[field] = by_id[ident]["fields"][field]
    return {"status": "EXECUTED_DECLARED_NODE", "fields": fields}


def authorize_transition(source, current, target, records):
    """Reject any runtime transition that is absent from the frozen source."""
    compiled = compile_source(source, records)
    allowed = compiled.get("graph", {}).get("edges", {}).get(current, [])
    if compiled["status"] != "CLOSED" or target not in allowed:
        return {"status": "UNKNOWN_KEEP", "allowed_targets": list(allowed)}
    return {"status": "AUTHORIZED", "allowed_targets": list(allowed)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    records = json.loads((SOURCE / "workload.json").read_text(encoding="utf-8-sig"))["records"]
    source = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    baseline = evaluate(source, records)
    current_payload = execute_node(source, "current", records)

    declared_consumer = copy.deepcopy(source)
    declared_consumer["nodes"]["effect"]["next"] = ["audit"]
    declared_consumer["nodes"]["audit"] = {
        "uses": [["completed-note", "terminal_receipt"]], "next": ["done"]
    }
    with_consumer = evaluate(declared_consumer, records)
    audit_payload = execute_node(declared_consumer, "audit", records)

    dynamic = copy.deepcopy(source)
    dynamic["nodes"]["effect"]["dynamic_read"] = "runtime-selected-record"
    unknown_dynamic = evaluate(dynamic, records)

    dangling = copy.deepcopy(source)
    dangling["nodes"]["effect"]["next"] = ["undeclared_callback"]
    unknown_edge = evaluate(dangling, records)

    tampered = copy.deepcopy(source)
    tampered["nodes"]["current"]["uses"].append(["completed-note", "terminal_receipt"])
    compiled = compile_source(source, records)
    changed_after_compile = evaluate(tampered, records, compiled["manifest_sha256"])

    unauthorized_transition = authorize_transition(source, "effect", "hidden_audit", records)
    unknown_dispatch = {
        "disposition": unauthorized_transition["status"],
        "selected_ids": [r["id"] for r in records] if unauthorized_transition["status"] == "UNKNOWN_KEEP" else [],
        "evicted_ids": [],
        "allowed_targets": unauthorized_transition["allowed_targets"],
    }
    raw = {
        "schema": "issue7367-closed-workflow-contract-a01-raw-v1",
        "base_main": "dd6143ef23033afcbfbd48d06d818d434d34d7d5",
        "a01_source_sha256": hashlib.sha256((SOURCE / "run_a01.py").read_bytes()).hexdigest(),
        "manifest_sha256": digest(source),
        "cases": {
            "baseline": baseline,
            "declared_node_execution": current_payload,
            "declared_hidden_consumer": with_consumer,
            "declared_hidden_consumer_execution": audit_payload,
            "unsupported_dynamic_read": unknown_dynamic,
            "unknown_successor": unknown_edge,
            "changed_after_compile": changed_after_compile,
            "unauthorized_dispatch": unknown_dispatch,
        },
        "limitation": "closed declarative machine workflow only; does not prove coverage of future user intent or arbitrary model-visible conversation",
    }
    Path(args.out).write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(raw, sort_keys=True))


if __name__ == "__main__":
    main()

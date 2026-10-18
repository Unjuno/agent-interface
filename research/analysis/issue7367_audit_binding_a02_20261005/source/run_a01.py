import argparse, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def visible_bytes(records, ids):
    selected = [r for r in records if r["id"] in ids]
    return len(json.dumps(selected, sort_keys=True, separators=(",", ":")).encode())

def analyze(workload, freeze, graph=None, records=None, scope=None):
    graph = graph or {"nodes": workload["nodes"], "edges": workload["edges"]}
    records = records or workload["records"]
    scope = scope or workload["scope"]
    by_id = {}
    integrity_error = False
    for r in records:
        ident = r.get("id")
        if ident in by_id and by_id[ident] != r:
            integrity_error = True
        by_id[ident] = r
    bad_effect = any(r.get("id") == "external-effect" and r.get("fields", {}).get("status") == "terminal" and not r.get("fields", {}).get("receipt_id") for r in records)
    graph_ok = digest({"nodes": graph["nodes"], "edges": graph["edges"]}) == freeze["graph_sha256"]
    if (not graph_ok or not scope.get("graph_complete", False) or scope.get("dynamic_consumers_possible", True) or integrity_error or bad_effect):
        return {"disposition": "UNKNOWN_KEEP", "reachable_nodes": [], "live_ids": [r["id"] for r in records], "selected_ids": [r["id"] for r in records], "evicted_ids": [], "reason": "graph_or_evidence_integrity_unproven"}
    reachable = set()
    pending = [workload["frontier"]]
    while pending:
        node = pending.pop()
        if node in reachable:
            continue
        if node not in graph["nodes"]:
            return {"disposition": "UNKNOWN_KEEP", "reachable_nodes": sorted(reachable), "live_ids": [r["id"] for r in records], "selected_ids": [r["id"] for r in records], "evicted_ids": [], "reason": "unknown_node"}
        reachable.add(node)
        pending.extend(graph["edges"].get(node, []))
    live = set()
    for node in reachable:
        for ident, field in graph["nodes"][node].get("uses", []):
            if ident not in by_id or field not in by_id[ident].get("fields", {}):
                return {"disposition": "UNKNOWN_KEEP", "reachable_nodes": sorted(reachable), "live_ids": [r["id"] for r in records], "selected_ids": [r["id"] for r in records], "evicted_ids": [], "reason": "unresolved_use"}
            live.add(ident)
    all_ids = [r["id"] for r in records]
    evicted = [ident for ident in all_ids if ident not in live]
    return {"disposition": "PROVEN_DEAD_EVICTION", "reachable_nodes": sorted(reachable), "live_ids": sorted(live), "selected_ids": sorted(live), "evicted_ids": sorted(evicted), "reason": "complete_graph_fixed_point"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    workload = json.loads((HERE / "workload.json").read_text(encoding="utf-8-sig"))
    freeze = json.loads((HERE / "PRE-RUN.json").read_text(encoding="utf-8-sig"))
    baseline = analyze(workload, freeze)
    records = workload["records"]
    all_ids = [r["id"] for r in records]
    ordered = sorted(records, key=lambda r: (r["created_seq"], r["id"]))
    policies = {
        "FULL_CONTEXT": all_ids,
        "RECENCY_BUDGET": [r["id"] for r in ordered[-workload["recency_budget_count"]:]],
        "TASK_CONDITIONED_RETRIEVAL": list(workload["task_conditioned_ids"]),
        "CONSERVATIVE_USE_LIVENESS": baseline["selected_ids"]
    }
    policy_rows = []
    for name, ids in policies.items():
        policy_rows.append({"policy": name, "selected_ids": sorted(set(ids)), "visible_bytes": visible_bytes(records, set(ids))})
    g = {"nodes": json.loads(json.dumps(workload["nodes"])), "edges": json.loads(json.dumps(workload["edges"]))}
    g["edges"]["current"].remove("recovery")
    terminal_records = json.loads(json.dumps(records))
    next(r for r in terminal_records if r["id"] == "external-effect")["fields"]["status"] = "terminal"
    alias_records = json.loads(json.dumps(records))
    alias_records.append({"id": "obs-v1", "version": 99, "created_seq": 12, "fields": {"health": 1}})
    historical_nodes = json.loads(json.dumps(workload["nodes"]))
    historical_nodes["current"]["uses"] = [["obs-v1", "health"], ["task-intent", "target"]]
    historical_graph = {"nodes": historical_nodes, "edges": workload["edges"]}
    dynamic_scope = {"graph_complete": True, "dynamic_consumers_possible": True}
    mutations = [
        {"id": "omitted-recovery-edge", "result": analyze(workload, freeze, graph=g)},
        {"id": "terminal-obligation-without-receipt", "result": analyze(workload, freeze, records=terminal_records)},
        {"id": "aliased-evidence-version", "result": analyze(workload, freeze, records=alias_records)},
        {"id": "current-consumer-changed-to-historical", "result": analyze(workload, freeze, graph=historical_graph)},
        {"id": "unmodeled-dynamic-consumer", "result": analyze(workload, freeze, scope=dynamic_scope)}
    ]
    raw = {"schema": "issue7367-a01-raw-v1", "base_analysis": baseline, "policies": policy_rows, "mutations": mutations,
           "canonical_record_sha256": {r["id"]: digest(r) for r in records}, "workload_sha256": hashlib.sha256((HERE/"workload.json").read_bytes()).hexdigest()}
    Path(args.out).write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"schema": raw["schema"], "base_disposition": baseline["disposition"], "evicted_ids": baseline["evicted_ids"], "policies": policy_rows, "mutation_dispositions": [{"id": m["id"], "disposition": m["result"]["disposition"], "evicted": m["result"]["evicted_ids"]} for m in mutations]}, sort_keys=True))

if __name__ == "__main__":
    main()

import argparse, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def canonical_sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def audit(raw_path, out_path):
    w = json.loads((HERE / "workload.json").read_text(encoding="utf-8-sig"))
    f = json.loads((HERE / "PRE-RUN.json").read_text(encoding="utf-8-sig"))
    r = json.loads(Path(raw_path).read_text(encoding="utf-8-sig"))
    checks = {}
    ids = [x["id"] for x in w["records"]]
    by_id = {x["id"]: x for x in w["records"]}
    # Separate oracle: enumerate the frozen continuation list, not the candidate's graph walk.
    required = set()
    continuation_uses = {}
    for path in w["continuations"]:
        path_ids = set()
        for node in path["nodes"]:
            if node not in w["nodes"]:
                checks["oracle_nodes_exist"] = False
                continue
            for evidence_id, field in w["nodes"][node].get("uses", []):
                if evidence_id not in by_id or field not in by_id[evidence_id].get("fields", {}):
                    checks["oracle_references_exist"] = False
                path_ids.add(evidence_id)
        continuation_uses[path["id"]] = sorted(path_ids)
        required |= path_ids
    checks["oracle_nodes_exist"] = checks.get("oracle_nodes_exist", True)
    checks["oracle_references_exist"] = checks.get("oracle_references_exist", True)
    base = r["base_analysis"]
    actual_live = set(base["selected_ids"])
    checks["complete_graph_declared"] = w["scope"] == {"graph_complete": True, "dynamic_consumers_possible": False}
    checks["all_enumerated_future_uses_retained"] = required <= actual_live
    checks["candidate_live_set_equals_independent_oracle"] = actual_live == required
    checks["dead_pruning_exists"] = bool(base["evicted_ids"])
    checks["only_independent_oracle_dead_ids_evicted"] = set(base["evicted_ids"]) <= (set(ids) - required)
    policy = {p["policy"]: p for p in r["policies"]}
    checks["liveness_context_smaller_than_full"] = policy["CONSERVATIVE_USE_LIVENESS"]["visible_bytes"] < policy["FULL_CONTEXT"]["visible_bytes"]
    checks["policy_names_complete"] = set(policy) == {"FULL_CONTEXT", "RECENCY_BUDGET", "TASK_CONDITIONED_RETRIEVAL", "CONSERVATIVE_USE_LIVENESS"}
    for p in policy.values():
        checks["canonical_evidence_unchanged"] = checks.get("canonical_evidence_unchanged", True) and all(canonical_sha(by_id[eid]) == r["canonical_record_sha256"][eid] for eid in p["selected_ids"])
    expected_mutations = {
        "omitted-recovery-edge": "UNKNOWN_KEEP",
        "terminal-obligation-without-receipt": "UNKNOWN_KEEP",
        "aliased-evidence-version": "UNKNOWN_KEEP",
        "current-consumer-changed-to-historical": "UNKNOWN_KEEP",
        "unmodeled-dynamic-consumer": "UNKNOWN_KEEP"
    }
    mutations = {m["id"]: m["result"] for m in r["mutations"]}
    checks["all_mutations_present"] = set(mutations) == set(expected_mutations)
    for mid, disposition in expected_mutations.items():
        result = mutations.get(mid, {})
        checks[mid+"_abstains"] = result.get("disposition") == disposition
        checks[mid+"_does_not_evict"] = result.get("evicted_ids") == [] and set(result.get("selected_ids", [])) >= set(ids)
    checks["workload_hash_matches"] = r["workload_sha256"] == hashlib.sha256((HERE/"workload.json").read_bytes()).hexdigest()
    checks["run_source_hash_matches_freeze"] = hashlib.sha256((HERE/"run_a01.py").read_bytes()).hexdigest() == f["source_sha256"]["run_a01.py"]
    checks["audit_source_hash_matches_freeze"] = hashlib.sha256((HERE/"audit_a01.py").read_bytes()).hexdigest() == f["source_sha256"]["audit_a01.py"]
    passed = all(checks.values())
    result = {"schema":"issue7367-a01-audit-v1","passed":passed,"classification":"PASS_METHOD_SCOPED" if passed else "FAIL_METHOD","checks":checks,"continuation_uses":continuation_uses,"independent_required_ids":sorted(required),"scope":"finite synthetic declared workflows only; no model/runtime/task effect"}
    Path(out_path).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return passed

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    raise SystemExit(0 if audit(args.raw, args.out) else 1)

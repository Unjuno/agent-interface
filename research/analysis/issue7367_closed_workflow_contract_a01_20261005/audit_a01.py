import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / "research/analysis/issue7367_context_liveness_a01_20261004"


def reachable_uses(manifest, records):
    pending = [manifest["entry"]]
    seen = set()
    uses = set()
    nodes = manifest["nodes"]
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        node = nodes[name]
        uses.update(tuple(x) for x in node["uses"])
        pending.extend(node["next"])
    by_id = {r["id"]: r for r in records}
    assert all(ident in by_id and field in by_id[ident]["fields"] for ident, field in uses)
    return {ident for ident, _field in uses}, seen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    records = json.loads((SOURCE / "workload.json").read_text(encoding="utf-8-sig"))["records"]
    all_ids = {r["id"] for r in records}
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    required, _nodes = reachable_uses(manifest, records)
    c = raw["cases"]
    declared_manifest = json.loads(json.dumps(manifest))
    declared_manifest["nodes"]["effect"]["next"] = ["audit"]
    declared_manifest["nodes"]["audit"] = {"uses": [["completed-note", "terminal_receipt"]], "next": ["done"]}
    declared_required, _ = reachable_uses(declared_manifest, records)
    checks = {
        "base_main_pinned": raw["base_main"] == "dd6143ef23033afcbfbd48d06d818d434d34d7d5",
        "candidate_source_hash_pinned": raw["a01_source_sha256"] == hashlib.sha256((SOURCE / "run_a01.py").read_bytes()).hexdigest(),
        "source_is_declared_complete_manifest": c["baseline"]["disposition"] == "PROVEN_DEAD_EVICTION",
        "independent_oracle_matches_baseline": set(c["baseline"]["selected_ids"]) == required,
        "manifest_consumers_keep_exact_records": set(c["declared_hidden_consumer"]["selected_ids"]) == declared_required and "completed-note" in declared_required,
        "interpreter_exposes_only_declared_reads": c["declared_node_execution"] == {
            "status": "EXECUTED_DECLARED_NODE",
            "fields": {"obs-v2": {"health": 68}, "task-intent": {"target": "finish-level"}},
        },
        "added_consumer_executes_only_its_declared_read": c["declared_hidden_consumer_execution"] == {
            "status": "EXECUTED_DECLARED_NODE", "fields": {"completed-note": {"terminal_receipt": "scan-4"}}
        },
        "unsupported_dynamic_read_fails_closed": c["unsupported_dynamic_read"]["disposition"] == "UNKNOWN_KEEP" and set(c["unsupported_dynamic_read"]["selected_ids"]) == all_ids,
        "unknown_successor_fails_closed": c["unknown_successor"]["disposition"] == "UNKNOWN_KEEP" and set(c["unknown_successor"]["selected_ids"]) == all_ids,
        "changed_manifest_fails_closed": c["changed_after_compile"]["disposition"] == "UNKNOWN_KEEP" and set(c["changed_after_compile"]["selected_ids"]) == all_ids,
        "undeclared_dispatch_fails_closed": c["unauthorized_dispatch"]["disposition"] == "UNKNOWN_KEEP" and set(c["unauthorized_dispatch"]["selected_ids"]) == all_ids and c["unauthorized_dispatch"]["allowed_targets"] == ["done"],
        "scope_limit_explicit": "does not prove coverage of future user intent" in raw["limitation"],
    }
    result = {"schema": "issue7367-closed-workflow-contract-a01-audit-v1", "passed": all(checks.values()), "checks": checks,
              "classification": "PASS_CLOSED_WORKFLOW_CONTRACT_SCOPED" if all(checks.values()) else "FAIL_AUDIT"}
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()

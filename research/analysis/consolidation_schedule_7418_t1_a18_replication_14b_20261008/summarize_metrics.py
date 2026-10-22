"""Recompute A16 checkpoint/cost metrics from preserved raw JSONL (no model calls)."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ARMS = ("episodic_only", "per_episode", "batch_2", "terminal")
SEEDS = (5701, 5702, 5703)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def exact(value, expected):
    return bool(isinstance(value, dict)
                and value.get("classification") == expected["classification"]
                and value.get("answer") == expected["answer"]
                and isinstance(value.get("source_ids"), list)
                and len(value["source_ids"]) == len(set(value["source_ids"]))
                and sorted(value["source_ids"]) == sorted(expected["source_ids"]))


def summarize(raw_path, queries_path, audit_path):
    raw_path, queries_path, audit_path = Path(raw_path), Path(queries_path), Path(audit_path)
    rows = [json.loads(line) for line in raw_path.read_text().splitlines() if line.strip()]
    queries = json.loads(queries_path.read_text())["queries"]
    audit = json.loads(audit_path.read_text())
    expected_by_id = {q["id"]: q for q in queries}
    query_bins = defaultdict(list)
    cost = defaultdict(lambda: {"calls": 0, "query_calls": 0, "consolidation_calls": 0,
                                "prompt_tokens": 0, "completion_tokens": 0,
                                "query_prompt_tokens": 0, "query_completion_tokens": 0,
                                "consolidation_prompt_tokens": 0, "consolidation_completion_tokens": 0,
                                "elapsed_ms": 0, "consolidation_elapsed_ms": 0,
                                "consolidation_memory_bytes": [], "query_errors": 0, "unknown_expected_queries": 0, "false_nonunknown_on_unknown": 0})
    for row in rows:
        key = (row["seed"], row["arm"])
        c = cost[key]
        c["calls"] += 1
        c["prompt_tokens"] += row["response"].get("prompt_eval_count", 0) or 0
        c["completion_tokens"] += row["response"].get("eval_count", 0) or 0
        c["elapsed_ms"] += row.get("elapsed_ms", 0) or 0
        if row["type"] == "query":
            c["query_calls"] += 1
            c["query_prompt_tokens"] += row["response"].get("prompt_eval_count", 0) or 0
            c["query_completion_tokens"] += row["response"].get("eval_count", 0) or 0
            try:
                observed = json.loads(row["response"]["response"])
            except (KeyError, TypeError, ValueError):
                observed = None
            hit = exact(observed, row["expected"])
            query_bins[(row["arm"], row["prefix"])].append(hit)
            c["query_errors"] += int(not hit)
            qid = row["query_id"]
            if qid == "q_rare_exception" and row["prefix"] >= 3:
                c.setdefault("rare_exception_queries", 0)
                c.setdefault("rare_exception_correct", 0)
                c["rare_exception_queries"] += 1
                c["rare_exception_correct"] += int(hit)
            if row["expected"]["classification"] == "UNKNOWN":
                c["unknown_expected_queries"] += 1
                if observed and observed.get("classification") in ("SUPPORTED", "FORBIDDEN", "CONFLICT"):
                    c["false_nonunknown_on_unknown"] += 1
        else:
            c["consolidation_calls"] += 1
            c["consolidation_prompt_tokens"] += row["response"].get("prompt_eval_count", 0) or 0
            c["consolidation_completion_tokens"] += row["response"].get("eval_count", 0) or 0
            c["consolidation_elapsed_ms"] += row.get("elapsed_ms", 0) or 0
            text = row["response"].get("response", "")
            c["consolidation_memory_bytes"].append({"prefix": row["prefix"], "bytes": len(text.encode("utf-8"))})
    checkpoint = {}
    for arm in ARMS:
        checkpoint[arm] = {}
        for prefix in range(1, 7):
            vals = query_bins[(arm, prefix)]
            checkpoint[arm][str(prefix)] = {"correct": sum(vals), "total": len(vals),
                                             "accuracy": sum(vals) / len(vals) if vals else None}
    per_checkpoint_query = {}
    for arm in ARMS:
        per_checkpoint_query[arm] = {}
        for prefix in range(1, 7):
            per_checkpoint_query[arm][str(prefix)] = {}
            for qid in expected_by_id:
                matches = []
                for row in rows:
                    if row["type"] == "query" and row["arm"] == arm and row["prefix"] == prefix and row["query_id"] == qid:
                        try: observed = json.loads(row["response"]["response"])
                        except (KeyError, TypeError, ValueError): observed = None
                        matches.append(exact(observed, row["expected"]))
                per_checkpoint_query[arm][str(prefix)][qid] = {"correct": sum(matches), "total": len(matches),
                                                               "accuracy": sum(matches) / len(matches) if matches else None}
    per_seed_accuracy = {}
    for seed in SEEDS:
        for arm in ARMS:
            vals = []
            for row in rows:
                if row["type"] == "query" and row["seed"] == seed and row["arm"] == arm:
                    try: observed = json.loads(row["response"]["response"])
                    except (KeyError, TypeError, ValueError): observed = None
                    vals.append(exact(observed, row["expected"]))
            per_seed_accuracy[f"{seed}/{arm}"] = sum(vals) / len(vals) if vals else None
    if per_seed_accuracy != audit["accuracies"]:
        for key, val in per_seed_accuracy.items():
            if abs(val - audit["accuracies"][key]) > 1e-12:
                raise AssertionError(f"independent accuracy reconstruction mismatch {key}: {val} vs {audit['accuracies'][key]}")
    result = {
        "status": "POSTHOC_DERIVED_METRICS",
        "source_raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "source_audit_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        "rows": len(rows),
        "independent_audit_status": audit["status"],
        "independent_audit_errors": len(audit["errors"]),
        "exact_accuracy_reconstruction_matches_auditor": True,
        "checkpoint_accuracy_by_arm": checkpoint,
        "checkpoint_query_accuracy_by_arm": per_checkpoint_query,
        "per_seed_accuracy": per_seed_accuracy,
        "per_seed_arm_cost": {f"{seed}/{arm}": cost[(seed,arm)] for seed in SEEDS for arm in ARMS},
        "definitions": {
            "checkpoint_accuracy": "Exact classification, answer, and duplicate-free source-id match to the frozen oracle, pooled over 3 seeds and 5 queries per arm/checkpoint.",
            "rare_exception_correct": "Exact q_rare_exception answer match at prefixes 3-6; this is not an executed action or safety event.",
            "false_nonunknown_on_unknown": "Query expected UNKNOWN but model returned SUPPORTED, FORBIDDEN, or CONFLICT.",
            "consolidation_memory_bytes": "UTF-8 bytes in each raw serialized consolidation response; one measured state per consolidation update.",
            "unsupported_transition_claims": "Zero when the frozen transition auditor reports zero errors; this checks this finite fixture only."
        },
        "unsupported_transition_claims": 0 if audit["status"] == "PASS_METHOD" and not audit["errors"] else None
    }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("queries")
    ap.add_argument("audit")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    result = summarize(args.raw, args.queries, args.audit)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"rows": result["rows"], "audit": result["independent_audit_status"],
                      "exact_accuracy_reconstruction_matches_auditor": result["exact_accuracy_reconstruction_matches_auditor"]}))

if __name__ == "__main__":
    main()

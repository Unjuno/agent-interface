"""Post-hoc review of A05 raw; does not modify the frozen candidate/auditor."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

PKG = Path(__file__).parent
RAW = PKG / "results/FORMAL_T1_A05/RAW.jsonl"
QUERIES = json.loads((PKG / "queries.json").read_text())["queries"]
LEDGER = json.loads((PKG / "episode_ledger.json").read_text())["episodes"]
EXPECTED_DIGEST = "500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41"
SEEDS = (4501, 4502, 4503)
ARMS = ("episodic_only", "per_episode", "batch_2", "terminal")
PREFIXES = (1, 2, 3, 4, 5, 6)


def valid_json(text):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None


rows = [json.loads(line) for line in RAW.read_text().splitlines() if line.strip()]
errors = []
if len(rows) != 390:
    errors.append(f"row count {len(rows)} != 390")
if [r.get("row_id") for r in rows] != list(range(len(rows))):
    errors.append("row_id sequence is not contiguous")
source_by_id = {e["id"]: set(e["source_ids"]) for e in LEDGER}
expected_by_id = {e["id"]: e for e in LEDGER}
transition = Counter()
consolidation_rows = []
query_scores = defaultdict(list)
all_call_metrics = defaultdict(lambda: {"calls":0,"prompt_tokens":0,"completion_tokens":0,"duration_ms":0})
for row in rows:
    key = (row.get("seed"), row.get("arm"), row.get("prefix"), row.get("type"), row.get("query_id"))
    req = row.get("request", {})
    resp = row.get("response", {})
    if req.get("model") != "qwen3:8b" or resp.get("model") != "qwen3:8b":
        errors.append(f"model name mismatch {key}")
    if row.get("model_tag_digest_before") != EXPECTED_DIGEST or row.get("model_tag_digest_after") != EXPECTED_DIGEST:
        errors.append(f"tag identity mismatch {key}")
    first = row.get("row_id") == 0
    if row.get("running_digest_before") != ("UNLOADED" if first else EXPECTED_DIGEST) or row.get("running_digest_after") != EXPECTED_DIGEST:
        errors.append(f"runner identity mismatch {key}")
    options = req.get("options", {})
    cap = 2048 if row.get("type") == "consolidation" else 128
    if options.get("num_predict") != cap or req.get("think") is not False:
        errors.append(f"decode cap/think mismatch {key}")
    if resp.get("done_reason") == "length":
        errors.append(f"length stop {key}")
    stats = all_call_metrics[(row.get("seed"), row.get("arm"))]
    stats["calls"] += 1
    stats["prompt_tokens"] += resp.get("prompt_eval_count", 0) or 0
    stats["completion_tokens"] += resp.get("eval_count", 0) or 0
    stats["duration_ms"] += row.get("elapsed_ms", 0) or 0
    if row.get("type") == "consolidation":
        consolidation_rows.append(row)
        state = valid_json(resp.get("response"))
        if not isinstance(state, dict) or not isinstance(state.get("claims"), list):
            errors.append(f"invalid consolidation JSON/schema {key}")
            continue
        claims = state["claims"]
        ids = [c.get("id") for c in claims]
        expected_ids = {e["id"] for e in LEDGER[:row["prefix"]]}
        if len(ids) != len(set(ids)) or set(ids) != expected_ids:
            transition["coverage_or_duplicate_failures"] += 1
        by_id = {c.get("id"): c for c in claims}
        for claim in claims:
            eid = claim.get("id")
            if eid not in source_by_id or set(claim.get("source_ids", [])) != source_by_id[eid]:
                transition["source_provenance_failures"] += 1
            elif eid in expected_by_id:
                episode = expected_by_id[eid]
                expected_value = episode.get("exact_effect", episode.get("value"))
                if eid == "ep06":
                    expected_value = "draft->published"
                if eid == "ep06":
                    expected_kind = "history_delta"
                elif eid == "ep03":
                    expected_kind = "forbidden_effect_exception"
                elif eid in ("ep01", "ep02"):
                    expected_kind = "verified_pattern"
                else:
                    expected_kind = "fact_observation"
                if claim.get("kind") != expected_kind or claim.get("value") != expected_value:
                    transition["semantic_faithfulness_failures"] += 1
        if row["prefix"] >= 3:
            exception = by_id.get("ep03")
            if exception and exception.get("kind") == "forbidden_effect_exception" and exception.get("value") == "no_external_effect" and set(exception.get("source_ids", [])) == {"src-03"}:
                transition["exception_preserved_states"] += 1
            else:
                transition["exception_missing_or_malformed"] += 1
            transition["exception_expected_states"] += 1
        if row["prefix"] >= 5:
            conflicts = [c for c in claims if c.get("kind") == "conflict" and c.get("key") == "revision-r7-mode" and c.get("value") == "UNKNOWN" and set(c.get("source_ids", [])) == {"src-04", "src-05"}]
            if not conflicts:
                transition["explicit_conflict_missing"] += 1
    else:
        value = valid_json(resp.get("response"))
        expected = row.get("expected", {})
        exact = bool(value is not None and value.get("classification") == expected.get("classification")
                     and value.get("answer") == expected.get("answer")
                     and isinstance(value.get("source_ids"), list)
                     and len(value["source_ids"]) == len(set(value["source_ids"]))
                     and sorted(value["source_ids"]) == sorted(expected.get("source_ids", [])))
        query_scores[(row["seed"], row["arm"])].append(exact)
accuracies = {f"{s}/{a}": sum(query_scores[(s,a)])/len(query_scores[(s,a)]) for s in SEEDS for a in ARMS}
contrasts = {}
qualifying = []
for i, a in enumerate(ARMS):
    for b in ARMS[i+1:]:
        ds = []
        for seed in SEEDS:
            delta = accuracies[f"{seed}/{a}"] - accuracies[f"{seed}/{b}"]
            ds.append(round(delta, 6)); contrasts[f"{seed}:{a}-{b}"] = round(delta, 6)
        if all(abs(d) >= .10 for d in ds) and (all(d > 0 for d in ds) or all(d < 0 for d in ds)):
            qualifying.append({"contrast": f"{a} vs {b}", "seed_differences": ds})
# Count consolidated states that have reached both contradictory facts.
transition["conflict_reviewed_states"] = sum(1 for r in consolidation_rows if r["prefix"] >= 5)
transition["history_states"] = sum(1 for r in consolidation_rows if r["prefix"] == 6)
transition["consolidation_states"] = len(consolidation_rows)
result = {
    "review_type": "post-hoc supplemental independent raw review; frozen candidate and frozen auditor unchanged",
    "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
    "rows": len(rows),
    "raw_integrity_errors": errors,
    "raw_integrity_status": "PASS" if not errors else "FAIL",
    "answer_accuracies": accuracies,
    "paired_accuracy_differences": contrasts,
    "all_call_metrics_including_consolidation": {f"{seed}/{arm}": all_call_metrics[(seed,arm)] for seed in SEEDS for arm in ARMS},
    "qualifying_answer_contrasts": qualifying,
    "answer_endpoint_decision": "PASS_CADENCE_SENSITIVITY_SCOPED" if qualifying and not errors else "UNCERTAIN",
    "transition_audit": dict(transition),
    "transition_audit_status": "PASS" if not any(transition[k] for k in ("coverage_or_duplicate_failures", "source_provenance_failures", "semantic_faithfulness_failures", "explicit_conflict_missing", "exception_missing_or_malformed")) else "FAIL",
    "overall_claim_status": "HOLD_NO_CLEAN_TRANSITION_AUDIT" if errors or transition["explicit_conflict_missing"] or transition["semantic_faithfulness_failures"] or transition["exception_missing_or_malformed"] else ("PASS_CADENCE_SENSITIVITY_SCOPED" if qualifying else "UNCERTAIN"),
    "interpretation": "Answer-level schedule sensitivity is independently reproduced. However, the prompt required explicit conflict objects and source-faithful history deltas. A raw scoring pass alone does not establish those transition properties.",
}
out = RAW.parent / "SUPPLEMENTAL_REVIEW.json"
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: result[k] for k in ("raw_integrity_status", "answer_endpoint_decision", "transition_audit", "transition_audit_status", "overall_claim_status", "qualifying_answer_contrasts")}, indent=2))

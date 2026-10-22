"""Independent raw-only audit for the frozen #8406 T1 model evaluation."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

ARMS = ("episodic_only", "per_episode", "batch_2", "terminal")
SEEDS = (4901, 4902, 4903)
PREFIXES = (1, 2, 3, 4, 5, 6)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def parse_response(record):
    try:
        text = record["response"]["response"]
        value = json.loads(text)
        if set(value) != {"classification", "answer", "source_ids"}:
            return None
        if not isinstance(value["source_ids"], list) or any(not isinstance(x, str) for x in value["source_ids"]):
            return None
        return value
    except (KeyError, TypeError, ValueError):
        return None



def validate_transition(memory, ledger, prefix, key):
    errors = []
    if not isinstance(memory, dict) or not isinstance(memory.get("claims"), list):
        return [f"invalid transition memory schema {key}"]
    claims = memory["claims"]
    ids = [c.get("id") for c in claims if isinstance(c, dict)]
    if len(ids) != len(claims) or len(ids) != len(set(ids)):
        errors.append(f"invalid or duplicate claim ids {key}")
        return errors
    visible = {episode["id"]: episode for episode in ledger[:prefix]}
    expected_ids = set(visible)
    expected_ids.update({"conflict:revision-r7-mode"} if {"ep04", "ep05"}.issubset(visible) else set())
    if set(ids) != expected_ids:
        errors.append(f"transition coverage mismatch {key}: {sorted(ids)} != {sorted(expected_ids)}")
    by_id = {claim["id"]: claim for claim in claims}
    for eid, episode in visible.items():
        claim = by_id.get(eid)
        if claim is None:
            continue
        if claim.get("source_ids") != episode["source_ids"]:
            errors.append(f"source provenance mismatch {key}/{eid}")
        if eid in ("ep01", "ep02"):
            expected = ("verified_pattern", "exact_effect", "draft_saved")
        elif eid == "ep03":
            expected = ("forbidden_effect_exception", "effects", "effect=no_external_effect; forbidden=publish")
        elif eid in ("ep04", "ep05"):
            expected = ("fact_observation", "revision-r7-mode", episode["value"])
        else:
            expected = ("history_delta", "revision-r8-mode", "draft->published")
        actual = (claim.get("kind"), claim.get("key"), claim.get("value"))
        if actual != expected:
            errors.append(f"unfaithful transition claim {key}/{eid}: {actual} != {expected}")
    conflict = by_id.get("conflict:revision-r7-mode")
    if {"ep04", "ep05"}.issubset(visible):
        expected_conflict = {"id":"conflict:revision-r7-mode", "kind":"conflict", "key":"revision-r7-mode", "value":"UNKNOWN", "source_ids":["src-04","src-05"]}
        if conflict != expected_conflict:
            errors.append(f"explicit conflict claim mismatch {key}")
    elif conflict is not None:
        errors.append(f"premature conflict claim {key}")
    valid_sources = {source for episode in ledger for source in episode["source_ids"]}
    for claim in claims:
        if not isinstance(claim.get("source_ids"), list) or any(source not in valid_sources for source in claim["source_ids"]):
            errors.append(f"unknown source id in transition {key}/{claim.get('id')}")
    return errors

def exact_score(value, expected):
    return bool(value is not None and value["classification"] == expected["classification"]
                and value["answer"] == expected["answer"]
                and len(value["source_ids"]) == len(set(value["source_ids"]))
                and sorted(value["source_ids"]) == sorted(expected["source_ids"]))


def audit(raw_path, queries, ledger, expected_digest):
    rows = [json.loads(line) for line in raw_path.read_text().splitlines() if line.strip()]
    errors = []
    by_key = {}
    for row in rows:
        key = (row.get("seed"), row.get("arm"), row.get("prefix"), row.get("type"), row.get("query_id"))
        if key in by_key:
            errors.append(f"duplicate row {key}")
        by_key[key] = row
        if row.get("request", {}).get("model") != "qwen3:8b": errors.append(f"wrong model {key}")
        if row.get("response", {}).get("model") != "qwen3:8b": errors.append(f"response model mismatch {key}")
        if row.get("model_digest") not in (None, expected_digest): errors.append(f"digest mismatch {key}")
        expected_before = "UNLOADED" if row.get("row_id") == 0 else expected_digest
        if row.get("running_digest_before") != expected_before or row.get("running_digest_after") != expected_digest:
            errors.append(f"loaded runner identity mismatch {key}")
        if row.get("model_tag_digest_before") != expected_digest or row.get("model_tag_digest_after") != expected_digest:
            errors.append(f"private tag identity mismatch {key}")
        options = row.get("request", {}).get("options", {})
        if row.get("request", {}).get("think") is not False: errors.append(f"thinking not disabled {key}")
        expected_cap = 2048 if row.get("type") == "consolidation" else 128
        if options.get("temperature") != 0.2 or options.get("top_p") != 0.9 or options.get("num_ctx") != 8192 or options.get("num_predict") != expected_cap:
            errors.append(f"decoding/context/output-cap drift {key}")
        if options.get("seed") != row.get("seed"): errors.append(f"seed mismatch {key}")
        if not isinstance(row.get("elapsed_ms"), int) or row["elapsed_ms"] < 0: errors.append(f"invalid timing {key}")
        if "prompt_eval_count" not in row.get("response", {}) or "eval_count" not in row.get("response", {}):
            errors.append(f"missing token accounting {key}")
    expected_query_count = len(SEEDS)*len(ARMS)*len(PREFIXES)*len(queries["queries"])
    expected_cons_count = len(SEEDS)*(6+3+1)
    if len(rows) != expected_query_count + expected_cons_count:
        errors.append(f"row count {len(rows)} != {expected_query_count+expected_cons_count}")

    scores = defaultdict(list)
    totals = defaultdict(lambda: {"calls":0,"prompt_tokens":0,"completion_tokens":0,"duration_ms":0,"errors":0})
    consolidation_counts = defaultdict(int)
    for seed in SEEDS:
        for arm in ARMS:
            memory = {"claims": []}
            last = 0
            for prefix in PREFIXES:
                due = arm == "per_episode" or (arm == "batch_2" and prefix % 2 == 0) or (arm == "terminal" and prefix == 6)
                if due:
                    row = by_key.get((seed,arm,prefix,"consolidation",None))
                    if row is None:
                        errors.append(f"missing consolidation {(seed,arm,prefix)}")
                    else:
                        batch_ids = [f"ep{i:02d}" for i in range(last+1,prefix+1)]
                        if row.get("input_episode_ids") != batch_ids: errors.append(f"consolidation episode mismatch {(seed,arm,prefix)}")
                        expected_batch = ledger[last:prefix]
                        if row.get("request", {}).get("prompt", "").find(canonical(expected_batch)) < 0:
                            errors.append(f"consolidation prompt/input mismatch {(seed,arm,prefix)}")
                        if row.get("request", {}).get("prompt", "").find(canonical(memory)) < 0:
                            errors.append(f"consolidation prompt/prior-memory mismatch {(seed,arm,prefix)}")
                        try:
                            memory = json.loads(row["response"]["response"])
                            errors.extend(validate_transition(memory, ledger, prefix, (seed,arm,prefix)))
                        except Exception:
                            memory = {"claims": []}
                            errors.append(f"invalid consolidation JSON {(seed,arm,prefix)}")
                        consolidation_counts[(seed,arm)] += 1
                    last = prefix
                for query in queries["queries"]:
                    row = by_key.get((seed,arm,prefix,"query",query["id"]))
                    if row is None:
                        errors.append(f"missing query {(seed,arm,prefix,query['id'])}")
                        continue
                    exp = query["expected_by_prefix"][str(prefix)]
                    value = parse_response(row)
                    score = exact_score(value, exp)
                    scores[(seed,arm)].append(score)
                    stats = totals[(seed,arm)]
                    stats["calls"] += 1
                    response = row.get("response", {})
                    stats["prompt_tokens"] += response.get("prompt_eval_count", 0) or 0
                    stats["completion_tokens"] += response.get("eval_count", 0) or 0
                    stats["duration_ms"] += row.get("elapsed_ms", 0) or 0
                    if response.get("error") or value is None: stats["errors"] += 1
                    if row.get("expected") != exp: errors.append(f"expected endpoint mismatch {(seed,arm,prefix,query['id'])}")
                    prompt = row.get("request", {}).get("prompt", "")
                    if query["question"] not in prompt or canonical(row.get("evidence")) not in prompt:
                        errors.append(f"query prompt/evidence mismatch {(seed,arm,prefix,query['id'])}")
                    if arm == "episodic_only":
                        expected_evidence = {"episodes":ledger[:prefix]}
                        if row.get("evidence") != expected_evidence: errors.append(f"episodic visibility mismatch {(seed,arm,prefix,query['id'])}")
                    else:
                        if row.get("evidence") != memory: errors.append(f"summary visibility mismatch {(seed,arm,prefix,query['id'])}")
    accuracies = {f"{seed}/{arm}":sum(vals)/len(vals) if vals else 0.0 for (seed,arm),vals in scores.items()}
    contrasts = {}
    for seed in SEEDS:
        for i, a in enumerate(ARMS):
            for b in ARMS[i+1:]:
                aa = sum(scores[(seed,a)])/len(scores[(seed,a)]) if scores[(seed,a)] else 0
                bb = sum(scores[(seed,b)])/len(scores[(seed,b)]) if scores[(seed,b)] else 0
                contrasts[f"{seed}:{a}-{b}"] = round(aa-bb,6)
    sensitivity = False
    labels = []
    for i,a in enumerate(ARMS):
        for b in ARMS[i+1:]:
            ds = [contrasts[f"{seed}:{a}-{b}"] for seed in SEEDS]
            if all(abs(d) >= 0.10 for d in ds) and (all(d>0 for d in ds) or all(d<0 for d in ds)):
                sensitivity = True; labels.append(f"{a} vs {b}: {ds}")
    max_abs = max((abs(x) for x in contrasts.values()), default=0)
    if errors: decision = "FAIL_METHOD"
    elif sensitivity: decision = "PASS_CADENCE_SENSITIVITY_SCOPED"
    elif max_abs < 0.10: decision = "PASS_NO_MATERIAL_CADENCE_EFFECT_SCOPED"
    else: decision = "UNCERTAIN"
    return {"status":"PASS_METHOD" if not errors else "FAIL_METHOD","errors":errors,"decision":decision,
            "rows":len(rows),"query_rows":expected_query_count,"consolidation_rows":expected_cons_count,
            "accuracies":accuracies,"paired_accuracy_differences":contrasts,"qualifying_consistent_contrasts":labels,
            "max_abs_accuracy_difference":max_abs,
            "per_seed_arm_metrics":{f"{seed}/{arm}":totals[(seed,arm)] for seed in SEEDS for arm in ARMS},
            "consolidation_updates_per_seed_arm":{f"{seed}/{arm}":consolidation_counts[(seed,arm)] for seed in SEEDS for arm in ARMS},
            "scope":"single synthetic ledger, one local model family, three fixed seeds; no GUI/product/action inference"}


def main():
    p=argparse.ArgumentParser(); p.add_argument("raw"); p.add_argument("queries"); p.add_argument("ledger"); p.add_argument("--model-digest",required=True); p.add_argument("--output",required=True); a=p.parse_args()
    ledger=json.loads(Path(a.ledger).read_text())["episodes"]
    result=audit(Path(a.raw),json.loads(Path(a.queries).read_text()),ledger,a.model_digest)
    Path(a.output).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"decision":result["decision"],"errors":len(result["errors"])}))


if __name__ == "__main__": main()

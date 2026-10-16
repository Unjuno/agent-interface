"""Independent raw-only reconstruction and audit for A19; performs no model calls."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

ARMS = ("episodic_only", "per_episode", "batch_2", "terminal")
SEEDS = (5801, 5802, 5803)
PREFIXES = (1, 2, 3, 4, 5, 6)
MODEL = "qwen3:14b"
FROZEN_DIGEST = "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"

# A separately maintained copy of the request schema is compared against every raw request.
CONSOLIDATION_SCHEMA = {
    "type": "object", "properties": {"claims": {"type": "array", "items": {
        "type": "object", "properties": {
            "id": {"type": "string"},
            "kind": {"type": "string", "enum": ["verified_pattern", "forbidden_effect_exception", "fact_observation", "history_delta", "conflict"]},
            "subject": {"type": "string"},
            "scope": {"type": "object", "properties": {"app": {"type": "string"}, "mode": {"type": "string"}, "surface": {"type": "string"}}, "required": ["app", "mode", "surface"], "additionalProperties": False},
            "fields": {"type": "object", "additionalProperties": {"type": "string"}, "minProperties": 1},
            "source_ids": {"type": "array", "items": {"type": "string"}},
        }, "required": ["id", "kind", "subject", "scope", "fields", "source_ids"], "additionalProperties": False,
    }}}, "required": ["claims"], "additionalProperties": False,
}
ANSWER_SCHEMA = {
    "type": "object", "properties": {"answers": {"type": "array", "minItems": 2, "maxItems": 2, "items": {
        "type": "object", "properties": {"query_id": {"type": "string"}, "classification": {"type": "string", "enum": ["SUPPORTED", "FORBIDDEN", "CONFLICT", "UNKNOWN"]},
                            "answer": {"type": ["string", "null"]}, "source_ids": {"type": "array", "items": {"type": "string"}}},
        "required": ["query_id", "classification", "answer", "source_ids"], "additionalProperties": False,
    }}}, "required": ["answers"], "additionalProperties": False,
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def schedule_due(arm, prefix):
    return arm == "per_episode" or (arm == "batch_2" and prefix % 2 == 0) or (arm == "terminal" and prefix == 6)


def facts_from_ledger(episodes):
    facts = []
    for episode in episodes:
        for fact in episode["facts"]:
            facts.append(fact)
    return facts


def reconstructed_memory(episodes):
    claims = [json.loads(json.dumps(fact)) for fact in facts_from_ledger(episodes)]
    groups = defaultdict(list)
    for claim in claims:
        if claim.get("kind") != "fact_observation":
            continue
        for field, value in claim.get("fields", {}).items():
            key = (claim.get("subject"), canonical(claim.get("scope")), field)
            groups[key].append((claim, value))
    for (subject, scope_text, field), entries in groups.items():
        values = {value for _, value in entries}
        if len(values) > 1:
            scope = json.loads(scope_text)
            sources = sorted({source for claim, _ in entries for source in claim["source_ids"]})
            claims.append({"id": f"conflict:{subject}:{field}", "kind": "conflict", "subject": subject, "scope": scope,
                           "fields": {field: "UNKNOWN"}, "source_ids": sources})
    return {"claims": sorted(claims, key=lambda claim: claim["id"])}


def visible_facts(evidence):
    if set(evidence) == {"episodes"}:
        return facts_from_ledger(evidence["episodes"])
    if set(evidence) == {"claims"}:
        return evidence["claims"]
    return []


def answer_from_visible_evidence(query, evidence):
    """Oracle uses only the evidence included in the query request, never the hidden ledger."""
    matching = []
    for fact in visible_facts(evidence):
        if fact.get("kind") == "conflict":
            continue
        if fact.get("subject") != query["subject"] or fact.get("scope") != query["scope"]:
            continue
        fields = fact.get("fields")
        if isinstance(fields, dict) and query["field"] in fields:
            matching.append((fact, fields[query["field"]]))
    if not matching:
        return {"query_id": query["id"], "classification": "UNKNOWN", "answer": None, "source_ids": []}
    values = {value for _, value in matching}
    kinds = {fact.get("kind") for fact, _ in matching}
    if len(values) > 1:
        if kinds == {"fact_observation"}:
            sources = sorted({source for fact, _ in matching for source in fact.get("source_ids", [])})
            return {"query_id": query["id"], "classification": "CONFLICT", "answer": None, "source_ids": sources}
        return {"query_id": query["id"], "classification": "UNKNOWN", "answer": None, "source_ids": []}
    classification = "FORBIDDEN" if query["field"] == "forbidden_effect" and kinds == {"forbidden_effect_exception"} else "SUPPORTED"
    sources = sorted({source for fact, _ in matching for source in fact.get("source_ids", [])})
    return {"query_id": query["id"], "classification": classification, "answer": next(iter(values)), "source_ids": sources}


def parse_json_response(row):
    try:
        return json.loads(row["response"]["response"])
    except (KeyError, TypeError, ValueError):
        return None


def exact_answer(actual, expected):
    return isinstance(actual, dict) and set(actual) == {"query_id", "classification", "answer", "source_ids"} \
        and actual.get("query_id") == expected["query_id"] \
        and actual.get("classification") == expected["classification"] \
        and actual.get("answer") == expected["answer"] \
        and isinstance(actual.get("source_ids"), list) \
        and sorted(actual["source_ids"]) == expected["source_ids"] \
        and len(actual["source_ids"]) == len(set(actual["source_ids"]))


def valid_answer_shape(actual, query_id):
    return isinstance(actual, dict) and set(actual) == {"query_id", "classification", "answer", "source_ids"} \
        and actual.get("query_id") == query_id \
        and actual.get("classification") in {"SUPPORTED", "FORBIDDEN", "CONFLICT", "UNKNOWN"} \
        and (actual.get("answer") is None or isinstance(actual.get("answer"), str)) \
        and isinstance(actual.get("source_ids"), list) \
        and all(isinstance(source, str) for source in actual["source_ids"]) \
        and len(actual["source_ids"]) == len(set(actual["source_ids"]))


def check_scope_contract(memory, key):
    errors = []
    if not isinstance(memory, dict) or not isinstance(memory.get("claims"), list):
        return [f"memory schema invalid at {key}"]
    ids = [claim.get("id") for claim in memory["claims"] if isinstance(claim, dict)]
    if len(ids) != len(memory["claims"]) or len(ids) != len(set(ids)):
        return [f"claim ids missing or duplicated at {key}"]
    for claim in memory["claims"]:
        scope = claim.get("scope")
        if not isinstance(scope, dict) or set(scope) != {"app", "mode", "surface"} or any(not isinstance(scope.get(k), str) or not scope[k] for k in ("app", "mode", "surface")):
            errors.append(f"incomplete applicability scope at {key}/{claim.get('id')}")
        if not isinstance(claim.get("fields"), dict) or not claim["fields"] or any(not isinstance(v, str) for v in claim["fields"].values()):
            errors.append(f"invalid claim fields at {key}/{claim.get('id')}")
    return errors


def audit(raw_path, ledger_doc, queries_doc, prompts_doc, expected_digest=FROZEN_DIGEST):
    ledger = ledger_doc["episodes"]
    queries = queries_doc["queries"]
    families = queries_doc["families"]
    errors, rows, by_key = [], [], {}
    try:
        for line_number, line in enumerate(Path(raw_path).read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except ValueError as error:
                    errors.append(f"invalid JSON line {line_number}: {error}")
    except OSError as error:
        return {"status": "FAIL_METHOD", "decision": "FAIL_METHOD", "errors": [f"cannot read raw: {error}"], "rows": 0}

    totals = defaultdict(lambda: {"calls": 0, "query_batches": 0, "query_items": 0, "prompt_tokens": 0, "completion_tokens": 0,
                                  "duration_ms": 0, "call_errors": 0, "answer_errors": 0,
                                  "visible_evidence_bytes_total": 0, "visible_evidence_bytes_max": 0})
    model_sizes = set()
    for row in rows:
        row_key = (row.get("seed"), row.get("arm"), row.get("prefix"), row.get("type"), row.get("family"))
        if row_key in by_key:
            errors.append(f"duplicate raw row {row_key}")
        by_key[row_key] = row
        stats = totals[(row.get("seed"), row.get("arm"))]
        stats["calls"] += 1
        stats["prompt_tokens"] += row.get("response", {}).get("prompt_eval_count", 0) or 0
        stats["completion_tokens"] += row.get("response", {}).get("eval_count", 0) or 0
        stats["duration_ms"] += row.get("elapsed_ms", 0) or 0
        if row.get("response", {}).get("error"):
            stats["call_errors"] += 1
        if row.get("request", {}).get("model") != MODEL or row.get("response", {}).get("model") != MODEL:
            errors.append(f"model tag mismatch {row_key}")
        if row.get("model_digest") != expected_digest:
            errors.append(f"frozen digest mismatch {row_key}")
        if not isinstance(row.get("model_size"), int) or row["model_size"] <= 0:
            errors.append(f"invalid model size receipt {row_key}")
        else:
            model_sizes.add(row["model_size"])
        expected_before = "UNLOADED" if row.get("row_id") == 0 else expected_digest
        if row.get("running_digest_before") != expected_before or row.get("running_digest_after") != expected_digest:
            errors.append(f"loaded model identity mismatch {row_key}")
        if row.get("model_tag_digest_before") != expected_digest or row.get("model_tag_digest_after") != expected_digest:
            errors.append(f"private model tag mismatch {row_key}")
        expected_schema = CONSOLIDATION_SCHEMA if row.get("type") == "consolidation" else ANSWER_SCHEMA
        request = row.get("request", {})
        if request.get("format") != expected_schema or request.get("think") is not False:
            errors.append(f"request schema/thinking drift {row_key}")
        if request.get("system") != prompts_doc["system"]:
            errors.append(f"system prompt drift {row_key}")
        options = request.get("options", {})
        cap = 4096 if row.get("type") == "consolidation" else 512
        if options.get("temperature") != 0.2 or options.get("top_p") != 0.9 or options.get("num_ctx") != 8192 or options.get("num_predict") != cap or options.get("seed") != row.get("seed"):
            errors.append(f"decoding drift {row_key}")
        if not isinstance(row.get("elapsed_ms"), int) or row["elapsed_ms"] < 0:
            errors.append(f"invalid duration {row_key}")
        if "prompt_eval_count" not in row.get("response", {}) or "eval_count" not in row.get("response", {}):
            errors.append(f"missing token accounting {row_key}")
    if len(model_sizes) > 1:
        errors.append("model size changed during allocation")

    query_call_count = len(SEEDS) * len(ARMS) * len(PREFIXES) * len(families)
    consolidation_count = len(SEEDS) * (6 + 3 + 1)
    if len(rows) != query_call_count + consolidation_count:
        errors.append(f"raw row count {len(rows)} != {query_call_count + consolidation_count}")
    if [row.get("row_id") for row in rows] != list(range(len(rows))):
        errors.append("row IDs are not the exact contiguous append order")

    scores, family_scores = defaultdict(list), defaultdict(list)
    transitions = defaultdict(int)
    for seed in SEEDS:
        for arm in ARMS:
            memory, last = {"claims": []}, 0
            for prefix in PREFIXES:
                if schedule_due(arm, prefix):
                    key = (seed, arm, prefix, "consolidation", None)
                    row = by_key.get(key)
                    if row is None:
                        errors.append(f"missing consolidation {key}")
                    else:
                        batch = ledger[last:prefix]
                        if row.get("input_episode_ids") != [episode["id"] for episode in batch]:
                            errors.append(f"consolidation batch IDs mismatch {key}")
                        prompt = row.get("request", {}).get("prompt", "")
                        expected_prompt = prompts_doc["consolidation_template"].replace("{{episodes}}", canonical(batch)).replace("{{memory}}", canonical(memory))
                        if prompt != expected_prompt:
                            errors.append(f"consolidation inputs/prior memory not visible in prompt {key}")
                        parsed = parse_json_response(row)
                        if not isinstance(parsed, dict) or not isinstance(parsed.get("claims"), list):
                            errors.append(f"invalid consolidation response {key}")
                        else:
                            errors.extend(check_scope_contract(parsed, key))
                            expected_memory = reconstructed_memory(ledger[:prefix])
                            actual_by_id = {claim.get("id"): claim for claim in parsed["claims"] if isinstance(claim, dict)}
                            if len(actual_by_id) != len(parsed["claims"]) or actual_by_id != {claim["id"]: claim for claim in expected_memory["claims"]}:
                                errors.append(f"source/value/scope transition mismatch {key}")
                            memory = parsed
                        transitions[(seed, arm)] += 1
                        last = prefix
                evidence = {"episodes": ledger[:prefix]} if arm == "episodic_only" else memory
                for family in families:
                    key = (seed, arm, prefix, "query", family)
                    row = by_key.get(key)
                    if row is None:
                        errors.append(f"missing query batch {key}")
                        continue
                    batch_queries = [query for query in queries if query["family"] == family]
                    if len(batch_queries) != 2 or row.get("query_ids") != [query["id"] for query in batch_queries]:
                        errors.append(f"query batch membership mismatch {key}")
                    if row.get("evidence") != evidence:
                        errors.append(f"query received unexpected visible evidence {key}")
                    evidence_bytes = len(canonical(evidence).encode("utf-8"))
                    if row.get("visible_evidence_bytes") != evidence_bytes:
                        errors.append(f"visible evidence byte count mismatch {key}")
                    prompt = row.get("request", {}).get("prompt", "")
                    expected_prompt = prompts_doc["query_template"].replace("{{queries}}", canonical(batch_queries)).replace("{{evidence}}", canonical(evidence))
                    if prompt != expected_prompt:
                        errors.append(f"query/evidence prompt mismatch {key}")
                    parsed = parse_json_response(row)
                    answer_map = {}
                    if not isinstance(parsed, dict) or not isinstance(parsed.get("answers"), list):
                        errors.append(f"invalid query response {key}")
                    else:
                        answer_map = {answer.get("query_id"): answer for answer in parsed["answers"] if isinstance(answer, dict)}
                        if len(answer_map) != 2 or set(answer_map) != {query["id"] for query in batch_queries}:
                            errors.append(f"query response IDs mismatch {key}")
                    stats = totals[(seed, arm)]
                    stats["query_batches"] += 1
                    stats["query_items"] += len(batch_queries)
                    stats["visible_evidence_bytes_total"] += evidence_bytes
                    stats["visible_evidence_bytes_max"] = max(stats["visible_evidence_bytes_max"], evidence_bytes)
                    if len(answer_map) != 2:
                        stats["call_errors"] += 1
                    for query in batch_queries:
                        expected = answer_from_visible_evidence(query, evidence)
                        actual = answer_map.get(query["id"])
                        if actual is not None and not valid_answer_shape(actual, query["id"]):
                            errors.append(f"answer response schema invalid {key}/{query['id']}")
                        is_correct = exact_answer(actual, expected)
                        scores[(seed, arm)].append(is_correct)
                        family_scores[(seed, arm, family)].append(is_correct)
                        if not is_correct:
                            stats["answer_errors"] += 1

    accuracy = {f"{seed}/{arm}": sum(scores[(seed, arm)])/len(scores[(seed, arm)]) if scores[(seed, arm)] else 0.0 for seed in SEEDS for arm in ARMS}
    by_family = {f"{seed}/{arm}/{family}": {"correct": sum(family_scores[(seed, arm, family)]), "items": len(family_scores[(seed, arm, family)])}
                 for seed in SEEDS for arm in ARMS for family in families}
    contrasts = {}
    for seed in SEEDS:
        for left_index, left in enumerate(ARMS):
            for right in ARMS[left_index+1:]:
                contrasts[f"{seed}:{left}-{right}"] = round(accuracy[f"{seed}/{left}"]-accuracy[f"{seed}/{right}"], 6)
    qualifying = []
    for left_index, left in enumerate(ARMS):
        for right in ARMS[left_index+1:]:
            differences = [contrasts[f"{seed}:{left}-{right}"] for seed in SEEDS]
            if all(abs(value) >= 0.10 for value in differences) and (all(value > 0 for value in differences) or all(value < 0 for value in differences)):
                qualifying.append({"contrast": f"{left}-{right}", "per_seed": differences})
    max_abs = max((abs(value) for value in contrasts.values()), default=0.0)
    if errors:
        decision = "FAIL_METHOD"
    elif qualifying:
        decision = "OBSERVED_CADENCE_CONTRAST_SCOPED"
    elif max_abs < 0.10:
        decision = "NO_10PP_CONTRAST_OBSERVED_SCOPED"
    else:
        decision = "UNCERTAIN"
    return {"status": "PASS_METHOD" if not errors else "FAIL_METHOD", "decision": decision, "errors": errors,
            "rows": len(rows), "query_batch_calls": query_call_count, "consolidation_calls": consolidation_count,
            "query_answer_items": len(SEEDS)*len(ARMS)*len(PREFIXES)*len(queries), "accuracy_by_seed_arm": accuracy,
            "accuracy_by_family": by_family, "paired_accuracy_differences": contrasts, "qualifying_contrasts": qualifying,
            "maximum_absolute_contrast": max_abs,
            "update_counts": {f"{seed}/{arm}": transitions[(seed, arm)] for seed in SEEDS for arm in ARMS},
            "costs": {f"{seed}/{arm}": totals[(seed, arm)] for seed in SEEDS for arm in ARMS},
            "scope": "one second synthetic corpus, one Qwen3 model/version, three preregistered seeds; no GUI, product, or action-effect claim"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("ledger")
    parser.add_argument("queries")
    parser.add_argument("prompts")
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-digest", default=FROZEN_DIGEST)
    args = parser.parse_args()
    result = audit(args.raw, json.loads(Path(args.ledger).read_text()), json.loads(Path(args.queries).read_text()),
                   json.loads(Path(args.prompts).read_text()), args.model_digest)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "decision": result["decision"], "errors": len(result["errors"])}))


if __name__ == "__main__":
    main()

"""Posthoc independent raw verifier for the completed A16 allocation.

This does not invoke the registered auditor or any model. It independently
reconstructs expected transitions and query inputs from the frozen package,
then recomputes exact-answer scores from preserved raw JSONL.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
SEEDS = (5601, 5602, 5603)
ARMS = ("episodic_only", "per_episode", "batch_2", "terminal")
PREFIXES = tuple(range(1, 7))
MODEL_DIGEST = "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"
RAW_SHA256 = "5d88e0a1cdfe05a99c5e2e42189fc47be611d7abf237e52fb5e556e3069881dd"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def consolidation_due(arm, prefix):
    return (arm == "per_episode"
            or (arm == "batch_2" and prefix % 2 == 0)
            or (arm == "terminal" and prefix == 6))


def expected_memory(ledger, prefix):
    claims = []
    for episode in ledger[:prefix]:
        kind = episode["kind"]
        if kind == "common_success":
            claim = {"id": episode["id"], "kind": "verified_pattern",
                     "key": "exact_effect", "value": episode["exact_effect"],
                     "source_ids": episode["source_ids"]}
        elif kind == "rare_exception":
            claim = {"id": episode["id"], "kind": "forbidden_effect_exception",
                     "key": "effects",
                     "value": f"effect={episode['exact_effect']}; forbidden={episode['forbidden_effect']}",
                     "source_ids": episode["source_ids"]}
        elif kind == "fact_observation":
            claim = {"id": episode["id"], "kind": "fact_observation",
                     "key": episode["fact_key"], "value": episode["value"],
                     "source_ids": episode["source_ids"]}
        elif kind == "history_pair":
            claim = {"id": episode["id"], "kind": "history_delta",
                     "key": f"{episode['version']}-mode",
                     "value": f"{episode['baseline']['mode']}->{episode['current']['mode']}",
                     "source_ids": [episode["baseline"]["source_id"],
                                    episode["current"]["source_id"]]}
        else:
            raise AssertionError(f"unrecognized frozen episode kind: {kind}")
        claims.append(claim)
    if prefix >= 5:
        claims.append({"id": "conflict:revision-r7-mode", "kind": "conflict",
                       "key": "revision-r7-mode", "value": "UNKNOWN",
                       "source_ids": ["src-04", "src-05"]})
    return {"claims": claims}


def normalized_memory(memory):
    if not isinstance(memory, dict) or set(memory) != {"claims"}:
        return None
    claims = memory["claims"]
    if not isinstance(claims, list) or any(not isinstance(c, dict) or "id" not in c for c in claims):
        return None
    ids = [c["id"] for c in claims]
    if len(ids) != len(set(ids)):
        return None
    return sorted(claims, key=lambda c: c["id"])


def parse_query_response(row):
    try:
        value = json.loads(row["response"]["response"])
    except (KeyError, TypeError, ValueError):
        return None
    if (not isinstance(value, dict)
            or set(value) != {"classification", "answer", "source_ids"}
            or not isinstance(value["source_ids"], list)
            or any(not isinstance(source, str) for source in value["source_ids"])):
        return None
    return value


def exact_match(value, expected):
    return (value is not None
            and value["classification"] == expected["classification"]
            and value["answer"] == expected["answer"]
            and len(value["source_ids"]) == len(set(value["source_ids"]))
            and sorted(value["source_ids"]) == sorted(expected["source_ids"]))


def run():
    package = json.loads((ROOT / "episode_ledger.json").read_text())
    ledger = package["episodes"]
    queries = json.loads((ROOT / "queries.json").read_text())["queries"]
    prompts = json.loads((ROOT / "prompts.json").read_text())
    frozen_audit = json.loads((ROOT / "results/FORMAL_T1_A16/audit.json").read_text())
    raw_path = ROOT / "results/FORMAL_T1_A16/raw.jsonl"
    raw_bytes = raw_path.read_bytes()
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    if raw_hash != RAW_SHA256:
        raise AssertionError(f"raw checksum mismatch: {raw_hash}")
    rows = [json.loads(line) for line in raw_bytes.splitlines() if line]

    errors = []
    transitions = []
    malformed_queries = []
    by_key = {}
    for row in rows:
        key = (row["seed"], row["arm"], row["prefix"], row["type"], row.get("query_id"))
        if key in by_key:
            errors.append(("duplicate_row", key))
        by_key[key] = row

    expected_keys = set()
    for seed in SEEDS:
        for arm in ARMS:
            for prefix in PREFIXES:
                if consolidation_due(arm, prefix):
                    expected_keys.add((seed, arm, prefix, "consolidation", None))
                for query in queries:
                    expected_keys.add((seed, arm, prefix, "query", query["id"]))
    if (len(rows) != 390 or set(by_key) != expected_keys
            or [row["row_id"] for row in rows] != list(range(390))):
        errors.append("row set, count, or row-id sequence mismatch")

    # Reconstruct each memory transition from the ledger, retaining the
    # observed order only when replaying the exact next request prompt.
    memory_at = {}
    for seed in SEEDS:
        for arm in ARMS:
            memory = {"claims": []}
            last_consolidated = 0
            for prefix in PREFIXES:
                if consolidation_due(arm, prefix):
                    row = by_key[(seed, arm, prefix, "consolidation", None)]
                    batch = ledger[last_consolidated:prefix]
                    prompt = (prompts["consolidation_template"]
                              .replace("{{episodes}}", canonical(batch))
                              .replace("{{memory}}", canonical(memory)))
                    if (row.get("input_episode_ids") != [e["id"] for e in batch]
                            or row.get("prior_memory") != memory
                            or row["request"].get("prompt") != prompt
                            or row["request"].get("system") != prompts["system"]):
                        errors.append(("transition_request_mismatch", seed, arm, prefix))
                    try:
                        observed = json.loads(row["response"]["response"])
                    except (KeyError, TypeError, ValueError):
                        observed = None
                    if normalized_memory(observed) != normalized_memory(expected_memory(ledger, prefix)):
                        transitions.append((seed, arm, prefix))
                        observed = expected_memory(ledger, prefix)
                    memory = observed
                    last_consolidated = prefix
                memory_at[(seed, arm, prefix)] = memory

    scores = Counter()
    for row in rows:
        seed, arm, prefix = row["seed"], row["arm"], row["prefix"]
        request = row["request"]
        response = row["response"]
        if (request.get("model") != "qwen3:14b"
                or response.get("model") != "qwen3:14b"
                or row.get("model_tag_digest_before") != MODEL_DIGEST
                or row.get("model_tag_digest_after") != MODEL_DIGEST
                or row.get("running_digest_after") != MODEL_DIGEST
                or row.get("running_digest_before") not in ("UNLOADED", MODEL_DIGEST)):
            errors.append(("model_identity_mismatch", row["row_id"]))
        options = request.get("options", {})
        cap = 2048 if row["type"] == "consolidation" else 128
        if (request.get("think") is not False
                or options.get("seed") != seed
                or options.get("temperature") != 0.2
                or options.get("top_p") != 0.9
                or options.get("num_ctx") != 8192
                or options.get("num_predict") != cap):
            errors.append(("request_setting_mismatch", row["row_id"]))
        if "error" in response:
            errors.append(("candidate_call_error", row["row_id"]))
        if row["type"] != "query":
            continue

        query = next(q for q in queries if q["id"] == row["query_id"])
        expected = query["expected_by_prefix"][str(prefix)]
        evidence = ({"episodes": ledger[:prefix]} if arm == "episodic_only"
                    else memory_at[(seed, arm, prefix)])
        expected_prompt = (prompts["query_template"]
                           .replace("{{query}}", query["question"])
                           .replace("{{evidence}}", canonical(evidence)))
        if (row.get("expected") != expected
                or row.get("evidence") != evidence
                or request.get("prompt") != expected_prompt
                or request.get("system") != prompts["system"]
                or request.get("format") != "json"):
            errors.append(("query_contract_mismatch", row["row_id"]))
        value = parse_query_response(row)
        if value is None:
            malformed_queries.append(row["row_id"])
        scores[(seed, arm)] += int(exact_match(value, expected))

    per_seed_accuracy = {
        f"{seed}/{arm}": scores[(seed, arm)] / 30
        for seed in SEEDS for arm in ARMS
    }
    for key, value in per_seed_accuracy.items():
        if abs(value - frozen_audit["accuracies"][key]) > 1e-12:
            errors.append(("frozen_accuracy_mismatch", key, value, frozen_audit["accuracies"][key]))
    if frozen_audit.get("status") != "PASS_METHOD" or frozen_audit.get("errors"):
        errors.append("frozen audit was not PASS_METHOD with zero errors")
    if errors or transitions or malformed_queries:
        raise AssertionError({"errors": errors[:10], "transitions": transitions[:10],
                              "malformed_queries": malformed_queries[:10]})
    return {
        "status": "POSTHOC_INDEPENDENT_CROSSCHECK_PASS",
        "source_commit": "6fc59c871a546494a44fbfd4645e2a9585fab970",
        "raw_sha256": raw_hash,
        "rows": len(rows),
        "transitions_checked": sum(consolidation_due(a, p) for a in ARMS for p in PREFIXES) * len(SEEDS),
        "query_responses_checked": sum(row["type"] == "query" for row in rows),
        "malformed_query_responses": len(malformed_queries),
        "transition_mismatches": len(transitions),
        "request_or_identity_mismatches": len(errors),
        "per_seed_accuracy": per_seed_accuracy,
        "accuracy_matches_frozen_audit": True,
        "frozen_audit_status": frozen_audit["status"],
        "frozen_audit_errors": len(frozen_audit["errors"]),
        "scope": "posthoc raw cross-check only; same fixture, model and seeds; no independent-corpus or product inference"
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))

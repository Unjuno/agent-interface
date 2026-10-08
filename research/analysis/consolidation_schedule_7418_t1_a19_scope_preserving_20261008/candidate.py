"""One-shot A19 candidate. Raw rows are append-only; no retry path exists."""
import argparse
import json
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

ARMS = ("episodic_only", "per_episode", "batch_2", "terminal")
SEEDS = (5801, 5802, 5803)
PREFIXES = (1, 2, 3, 4, 5, 6)
MODEL = "qwen3:14b"
EXPECTED_DIGEST = "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"

CLAIM_SCHEMA = {
    "type": "object", "properties": {
        "id": {"type": "string"},
        "kind": {"type": "string", "enum": ["verified_pattern", "forbidden_effect_exception", "fact_observation", "history_delta", "conflict"]},
        "subject": {"type": "string"},
        "scope": {"type": "object", "properties": {"app": {"type": "string"}, "mode": {"type": "string"}, "surface": {"type": "string"}}, "required": ["app", "mode", "surface"], "additionalProperties": False},
        "fields": {"type": "object", "additionalProperties": {"type": "string"}, "minProperties": 1},
        "source_ids": {"type": "array", "items": {"type": "string"}},
    }, "required": ["id", "kind", "subject", "scope", "fields", "source_ids"], "additionalProperties": False,
}
CONSOLIDATION_SCHEMA = {"type": "object", "properties": {"claims": {"type": "array", "items": CLAIM_SCHEMA}}, "required": ["claims"], "additionalProperties": False}
ANSWER_SCHEMA = {
    "type": "object", "properties": {"answers": {"type": "array", "minItems": 2, "maxItems": 2, "items": {
        "type": "object", "properties": {
            "query_id": {"type": "string"},
            "classification": {"type": "string", "enum": ["SUPPORTED", "FORBIDDEN", "CONFLICT", "UNKNOWN"]},
            "answer": {"type": ["string", "null"]},
            "source_ids": {"type": "array", "items": {"type": "string"}},
        }, "required": ["query_id", "classification", "answer", "source_ids"], "additionalProperties": False,
    }}}, "required": ["answers"], "additionalProperties": False,
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def request_body(prompts, operation, seed):
    if operation["kind"] == "consolidate":
        prompt = prompts["consolidation_template"].replace("{{episodes}}", canonical(operation["episodes"])).replace("{{memory}}", canonical(operation["memory"]))
        output_format, limit = CONSOLIDATION_SCHEMA, 4096
    else:
        prompt = prompts["query_template"].replace("{{queries}}", canonical(operation["queries"])).replace("{{evidence}}", canonical(operation["evidence"]))
        output_format, limit = ANSWER_SCHEMA, 512
    return {
        "model": MODEL, "system": prompts["system"], "prompt": prompt, "stream": False,
        "format": output_format, "think": False, "keep_alive": "30m",
        "options": {"seed": seed, "temperature": 0.2, "top_p": 0.9, "num_ctx": 8192, "num_predict": limit},
    }


def post_json(url, payload):
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=900) as response:
        return json.loads(response.read())


def load_model_tag(base_url):
    with urllib.request.urlopen(base_url + "/api/tags", timeout=10) as response:
        models = json.loads(response.read()).get("models", [])
    matches = [entry for entry in models if entry.get("name") == MODEL]
    if len(matches) != 1:
        raise RuntimeError("expected exactly one private Qwen3 14B tag")
    return matches[0].get("digest"), matches[0].get("size")


def load_running_model(base_url):
    with urllib.request.urlopen(base_url + "/api/ps", timeout=10) as response:
        models = json.loads(response.read()).get("models", [])
    matches = [entry for entry in models if entry.get("name") == MODEL]
    if not matches:
        return None, None, "UNLOADED"
    if len(matches) != 1:
        raise RuntimeError("expected at most one running private Qwen3 14B process")
    return matches[0].get("digest"), matches[0].get("size"), matches[0].get("name")


def run(ledger_doc, queries_doc, prompts, raw_path, base_url= "http://127.0.0.1:11435"):
    tag_digest, tag_size = load_model_tag(base_url)
    if tag_digest != EXPECTED_DIGEST:
        raise RuntimeError("private model tag differs from the frozen digest")
    running_digest, _, _ = load_running_model(base_url)
    if running_digest not in (None, EXPECTED_DIGEST):
        raise RuntimeError("loaded model differs from the frozen digest")
    if running_digest is not None:
        raise RuntimeError("private model must be unloaded before the one-shot candidate starts")

    episodes = ledger_doc["episodes"]
    families = queries_doc["families"]
    grouped = defaultdict(list)
    for query in queries_doc["queries"]:
        grouped[query["family"]].append(query)
    if tuple(families) != ("common", "rare_exception", "conflict", "history", "heldout") or any(len(grouped[name]) != 2 for name in families):
        raise RuntimeError("frozen query batches must contain two queries in each of five families")

    row_id = 0
    with Path(raw_path).open("x", encoding="utf-8") as raw:
        def invoke(record, payload):
            tag_before, _ = load_model_tag(base_url)
            digest_before, _, name_before = load_running_model(base_url)
            if tag_before != EXPECTED_DIGEST or digest_before not in (None, EXPECTED_DIGEST):
                record.update(response={"error": "model identity mismatch before request", "model": MODEL}, elapsed_ms=0,
                              model_tag_digest_before=tag_before, running_digest_before=digest_before or "UNLOADED")
                raw.write(canonical(record) + "\n"); raw.flush()
                raise RuntimeError("model identity mismatch before request")
            record.update(model_tag_digest_before=tag_before, running_digest_before=digest_before or "UNLOADED", running_model_name_before=name_before)
            started = time.monotonic_ns()
            try:
                response = post_json(base_url + "/api/generate", payload)
            except Exception as error:
                record.update(response={"error": f"{type(error).__name__}: {error}", "model": MODEL}, elapsed_ms=(time.monotonic_ns()-started)//1_000_000)
                raw.write(canonical(record) + "\n"); raw.flush()
                raise
            record["response"] = response
            record["elapsed_ms"] = (time.monotonic_ns()-started)//1_000_000
            try:
                tag_after, _ = load_model_tag(base_url)
                digest_after, _, name_after = load_running_model(base_url)
            except Exception as error:
                tag_after, digest_after, name_after = "UNAVAILABLE", "UNAVAILABLE", f"{type(error).__name__}: {error}"
            record.update(model_tag_digest_after=tag_after, running_digest_after=digest_after, running_model_name_after=name_after)
            raw.write(canonical(record) + "\n"); raw.flush()
            if tag_after != EXPECTED_DIGEST or digest_after != EXPECTED_DIGEST:
                raise RuntimeError("model identity changed or became unavailable after request")
            return response

        for seed in SEEDS:
            for arm in ARMS:
                memory, last = {"claims": []}, 0
                for prefix in PREFIXES:
                    due = arm == "per_episode" or (arm == "batch_2" and prefix % 2 == 0) or (arm == "terminal" and prefix == 6)
                    if due:
                        batch = episodes[last:prefix]
                        operation = {"kind": "consolidate", "episodes": batch, "memory": memory}
                        payload = request_body(prompts, operation, seed)
                        record = {"row_id": row_id, "type": "consolidation", "seed": seed, "arm": arm, "prefix": prefix,
                                  "input_episode_ids": [episode["id"] for episode in batch], "prior_memory": memory,
                                  "request": payload, "model_digest": tag_digest, "model_size": tag_size}
                        response = invoke(record, payload)
                        memory = json.loads(response["response"])
                        row_id += 1
                        last = prefix
                    evidence = {"episodes": episodes[:prefix]} if arm == "episodic_only" else memory
                    for family in families:
                        batch_queries = grouped[family]
                        operation = {"kind": "query", "queries": batch_queries, "evidence": evidence}
                        payload = request_body(prompts, operation, seed)
                        record = {"row_id": row_id, "type": "query", "seed": seed, "arm": arm, "prefix": prefix,
                                  "family": family, "query_ids": [query["id"] for query in batch_queries],
                                  "evidence": evidence, "visible_evidence_bytes": len(canonical(evidence).encode("utf-8")),
                                  "request": payload, "model_digest": tag_digest, "model_size": tag_size}
                        invoke(record, payload)
                        row_id += 1
    return row_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:11435")
    args = parser.parse_args()
    package = Path(args.package)
    rows = run(json.loads((package/"episode_ledger.json").read_text()), json.loads((package/"queries.json").read_text()),
               json.loads((package/"prompts.json").read_text()), args.raw, args.base_url)
    print(f"candidate completed {rows} model calls; expected 390")


if __name__ == "__main__":
    main()

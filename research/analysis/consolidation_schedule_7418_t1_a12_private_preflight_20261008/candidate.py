"""One-shot model-facing T1 schedule evaluation runner; raw output is append-only JSONL."""
import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

ARMS = ("episodic_only", "per_episode", "batch_2", "terminal")
CHECKPOINTS = (1, 2, 3, 4, 5, 6)
SEEDS = (5201, 5202, 5203)
MODEL = "qwen3:8b"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def request_body(model, prompts, operation, seed, num_predict):
    if operation["kind"] == "consolidate":
        prompt = prompts["consolidation_template"].replace("{{episodes}}", canonical(operation["episodes"])).replace("{{memory}}", canonical(operation["memory"]))
        limit = 2048
    else:
        prompt = prompts["query_template"].replace("{{query}}", operation["question"]).replace("{{evidence}}", canonical(operation["evidence"]))
        limit = 128
    return {
        "model": MODEL,
        "system": prompts["system"],
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "think": False,
        "keep_alive": "30m",
        "options": {"seed": seed, "temperature": 0.2, "top_p": 0.9, "num_ctx": 8192, "num_predict": min(limit, num_predict)},
    }


def post_json(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=900) as response:
        return json.loads(response.read())


def load_model_tag(base_url):
    with urllib.request.urlopen(base_url + "/api/tags", timeout=10) as response:
        tags = json.loads(response.read()).get("models", [])
    matches = [m for m in tags if m.get("name") == MODEL]
    if len(matches) != 1:
        raise RuntimeError("expected exactly one private model tag")
    return matches[0].get("digest"), matches[0].get("size")


def load_running_model(base_url):
    with urllib.request.urlopen(base_url + "/api/ps", timeout=10) as response:
        tags = json.loads(response.read()).get("models", [])
    matches = [m for m in tags if m.get("name") == MODEL]
    if not matches:
        return None, None, "UNLOADED"
    if len(matches) != 1:
        raise RuntimeError("expected at most one running model process")
    return matches[0].get("digest"), matches[0].get("size"), matches[0].get("name")


def run(model, prompts, queries, raw_path, base_url, expected_digest):
    digest, size = load_model_tag(base_url)
    if digest != expected_digest:
        raise RuntimeError("private model tag digest differs from frozen digest")
    running_digest, _, running_name = load_running_model(base_url)
    if running_digest not in (None, expected_digest):
        raise RuntimeError("loaded model digest differs from frozen digest")
    ledger = model["episodes"]
    row_index = 0
    with raw_path.open("x", encoding="utf-8") as raw:
        def invoke(record, payload):
            tag_before, _ = load_model_tag(base_url)
            current_digest, _, current_name = load_running_model(base_url)
            if tag_before != expected_digest or current_digest not in (None, expected_digest):
                record["response"] = {"error":"private model identity changed before request","model":MODEL}
                record["elapsed_ms"] = 0
                record["model_tag_digest_before"] = tag_before
                record["running_digest_before"] = current_digest or "UNLOADED"
                raw.write(canonical(record)+"\n"); raw.flush()
                raise RuntimeError("private model identity changed before request")
            record["running_model_name"] = current_name
            record["running_digest_before"] = current_digest or "UNLOADED"
            record["model_tag_digest_before"] = tag_before
            started = time.monotonic_ns()
            try:
                response = post_json(base_url + "/api/generate", payload)
            except Exception as error:
                record["response"] = {"error":f"{type(error).__name__}: {error}","model":MODEL}
                record["elapsed_ms"] = (time.monotonic_ns() - started) // 1_000_000
                raw.write(canonical(record)+"\n"); raw.flush()
                raise
            record["response"] = response
            record["elapsed_ms"] = (time.monotonic_ns() - started) // 1_000_000
            try:
                tag_after, _ = load_model_tag(base_url)
                after_digest, _, after_name = load_running_model(base_url)
            except Exception as error:
                tag_after, after_digest, after_name = "UNAVAILABLE", "UNAVAILABLE", "UNAVAILABLE"
                record["post_call_identity_error"] = f"{type(error).__name__}: {error}"
            record["model_tag_digest_after"] = tag_after
            record["running_digest_after"] = after_digest
            record["running_model_name_after"] = after_name
            raw.write(canonical(record)+"\n"); raw.flush()
            if tag_after != expected_digest or after_digest != expected_digest:
                raise RuntimeError("private model identity changed after generation")
            return response
        for seed_i, seed in enumerate(SEEDS):
            for arm_i in range(len(ARMS)):
                arm = ARMS[(arm_i + seed_i) % len(ARMS)]
                memory = {"claims": []}
                last_consolidated = 0
                for prefix in CHECKPOINTS:
                    visible_episodes = ledger[:prefix]
                    due = (arm == "per_episode" or (arm == "batch_2" and prefix % 2 == 0) or (arm == "terminal" and prefix == 6))
                    if due:
                        batch = ledger[last_consolidated:prefix]
                        operation = {"kind":"consolidate","episodes":batch,"memory":memory}
                        payload = request_body(model, prompts, operation, seed, 2048)
                        record = {"row_id":row_index,"type":"consolidation","seed":seed,"arm":arm,"prefix":prefix,"input_episode_ids":[e["id"] for e in batch],"prior_memory":memory,"request":payload}
                        response = invoke(record,payload)
                        row_index += 1
                        memory = json.loads(response["response"])
                        last_consolidated = prefix
                    evidence = {"episodes":visible_episodes} if arm == "episodic_only" else memory
                    for query in queries["queries"]:
                        operation = {"kind":"query","question":query["question"],"evidence":evidence}
                        payload = request_body(model, prompts, operation, seed, 128)
                        record = {"row_id":row_index,"type":"query","seed":seed,"arm":arm,"prefix":prefix,"query_id":query["id"],"expected":query["expected_by_prefix"][str(prefix)],"evidence":evidence,"request":payload,"model_digest":digest,"model_size":size}
                        invoke(record,payload)
                        row_index += 1
    return row_index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:11435")
    parser.add_argument("--model-digest", required=True)
    args = parser.parse_args()
    package = Path(args.package)
    model = json.loads((package / "episode_ledger.json").read_text())
    prompts = json.loads((package / "prompts.json").read_text())
    queries = json.loads((package / "queries.json").read_text())
    count = run(model, prompts, queries, Path(args.raw), args.base_url, args.model_digest)
    print(f"candidate completed {count} model calls; expected 390")


if __name__ == "__main__":
    main()

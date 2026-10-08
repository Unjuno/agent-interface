#!/usr/bin/env python3
"""One-shot network-attached, GPU-less client for the isolated Ollama service."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "qwen2.5vl:3b"
FORMAT = {
    "type": "object",
    "properties": {
        "present": {"type": "boolean"},
        "point": {"anyOf": [{"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2}, {"type": "null"}]},
    },
    "required": ["present", "point"], "additionalProperties": False,
}


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def get_json(url: str, timeout: int = 15):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post_json(url: str, value, timeout: int = 300):
    req = urllib.request.Request(url, data=canonical(value), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["construction", "formal"], required=True)
    ap.add_argument("--inputs", default="/inputs")
    ap.add_argument("--output", default="/out")
    args = ap.parse_args()
    inputs, out = Path(args.inputs), Path(args.output)
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY_OR_MISSING")
    manifest = json.loads((inputs / "manifest.json").read_text(encoding="utf-8"))
    rows = [x for x in manifest["rows"] if x["split"] == args.split]
    host = os.environ.get("OLLAMA_HOST", "http://ollama-r8:11434").rstrip("/")
    tags = get_json(host + "/api/tags")
    models = [m for m in tags.get("models", []) if m.get("name") == MODEL]
    if len(models) != 1 or models[0].get("digest") != "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1":
        raise SystemExit("STOP_MODEL_IDENTITY_MISMATCH")
    (out / "preflight.json").write_text(json.dumps({"tags_model": models[0], "ps_before": get_json(host + "/api/ps")}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    records = []
    for index, row in enumerate(rows):
        raw = (inputs / row["source_file"]).read_bytes()
        edge = (inputs / row["edge_file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["source_sha256"] or hashlib.sha256(edge).hexdigest() != row["edge_sha256"]:
            raise SystemExit("STOP_INPUT_HASH_MISMATCH:" + row["case_id"])
        for arm in ((["RAW", "EDGE"] if index % 2 == 0 else ["EDGE", "RAW"])):
            images = [base64.b64encode(raw).decode("ascii")]
            if arm == "EDGE":
                images.append(base64.b64encode(edge).decode("ascii"))
            payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": row["prompt"], "images": images}],
                "stream": False, "format": FORMAT,
                "options": {"temperature": 0, "seed": row["seed"], "top_p": 1, "top_k": 1, "num_ctx": 8192, "num_predict": 128},
                "keep_alive": "10m",
            }
            ps_pre = get_json(host + "/api/ps")
            start_ns = time.time_ns()
            response = post_json(host + "/api/chat", payload)
            end_ns = time.time_ns()
            ps_post = get_json(host + "/api/ps")
            records.append({
                "case_id": row["case_id"], "split": args.split, "arm": arm,
                "start_ns": start_ns, "end_ns": end_ns,
                "request_sha256": hashlib.sha256(canonical(payload)).hexdigest(),
                "request": payload, "response": response,
                "ollama_ps_pre": ps_pre, "ollama_ps_post": ps_post,
            })
            print(json.dumps({"case_id": row["case_id"], "arm": arm, "start_ns": start_ns, "end_ns": end_ns}, separators=(",", ":")), flush=True)
    with (out / "raw_calls.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    summary = {"split": args.split, "calls": len(records), "model": MODEL, "model_digest": models[0]["digest"], "output_sha256": hashlib.sha256((out / "raw_calls.jsonl").read_bytes()).hexdigest()}
    (out / "runner_summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

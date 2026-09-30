from __future__ import annotations

import argparse
import base64
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


MODEL = "qwen2.5vl:3b"
EXPECTED_DIGEST = "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"
SCHEMA = {
    "type": "object",
    "properties": {
        "present": {"type": "boolean"},
        "box": {"type": ["array", "null"], "items": {"type": "integer"}, "minItems": 4, "maxItems": 4},
    },
    "required": ["present", "box"],
    "additionalProperties": False,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def post_json(url: str, obj: dict, timeout: int = 300) -> dict:
    raw = json.dumps(obj, separators=(",", ":")).encode()
    req = urllib.request.Request(url, data=raw, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["identity", "construction", "formal"], required=True)
    p.add_argument("--url", default="http://ollama:11434")
    p.add_argument("--data", type=Path, default=Path("/data"))
    p.add_argument("--out", type=Path, default=Path("/out"))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.mode == "identity":
        tags = get_json(args.url + "/api/tags")
        matches = [m for m in tags.get("models", []) if m.get("name") == MODEL]
        result = {"models": matches, "expected_model": MODEL, "expected_digest": EXPECTED_DIGEST}
        (args.out / "model_identity.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if len(matches) != 1 or matches[0].get("digest") != EXPECTED_DIGEST:
            raise SystemExit("cached model digest mismatch; no inference requested")
        print(json.dumps({"model": MODEL, "digest": matches[0]["digest"], "capabilities": matches[0].get("capabilities")}))
        return
    pre = json.loads((args.data / "PREFORMAL.json").read_text(encoding="utf-8"))
    if args.mode == "construction":
        case = pre["construction_case"]
    else:
        for case in pre["formal_cases"]:
            image_path = args.data / case["image_path"]
            request = {
                "model": MODEL,
                "messages": [{"role": "user", "content": pre["prompt"], "images": [base64.b64encode(image_path.read_bytes()).decode("ascii")]}],
                "format": SCHEMA,
                "stream": False,
                "keep_alive": "5m",
                "options": {"temperature": 0, "seed": case["seed"], "num_predict": 128},
            }
            record_one(args, pre, case, request)
        print(json.dumps({"formal_requests": len(pre["formal_cases"]), "result": "complete"}))
        return
    image_path = args.data / case["image_path"]
    request = {
        "model": MODEL,
        "messages": [{"role": "user", "content": pre["prompt"], "images": [base64.b64encode(image_path.read_bytes()).decode("ascii")]}],
        "format": SCHEMA,
        "stream": False,
        "keep_alive": "5m",
        "options": {"temperature": 0, "seed": case["seed"], "num_predict": 128},
    }
    record_one(args, pre, case, request)
    print(json.dumps({"construction_request": 1, "case_id": case["case_id"]}))


def record_one(args, pre: dict, case: dict, request: dict) -> None:
    image_path = args.data / case["image_path"]
    image_bytes = image_path.read_bytes()
    start_ns = time.time_ns()
    error = None
    response = None
    try:
        response = post_json(args.url + "/api/chat", request)
    except Exception as exc:  # retain the single failed attempt; never retry
        error = f"{type(exc).__name__}: {exc}"
    end_ns = time.time_ns()
    out_dir = args.out / ("construction" if args.mode == "construction" else "formal")
    out_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "schema": "visual-encoding-570-local-r4-raw-call-v1",
        "mode": args.mode,
        "case_id": case["case_id"],
        "seed": case["seed"],
        "model": MODEL,
        "expected_digest": EXPECTED_DIGEST,
        "request": request,
        "request_sha256": sha(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()),
        "image_sha256": sha(image_bytes),
        "prompt_sha256": pre["prompt_sha256"],
        "started_utc_ns": start_ns,
        "ended_utc_ns": end_ns,
        "response": response,
        "error": error,
    }
    path = out_dir / f"{case['case_id']}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if error:
        raise SystemExit(f"one-shot request failed for {case['case_id']}; attempt retained; no retry: {error}")


if __name__ == "__main__":
    main()


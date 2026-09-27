"""Host-local Ollama file RPC; formal mode never accepts a remote endpoint."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import time
import urllib.request


MODEL = "qwen2.5vl:7b"
DIGEST = "5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc"
ENDPOINT = "http://127.0.0.1:11434"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def get_json(path):
    with urllib.request.urlopen(ENDPOINT + path, timeout=10) as response:
        return json.loads(response.read())


def check_model():
    rows = get_json("/api/tags")["models"]
    matches = [row for row in rows if row.get("name") == MODEL]
    if len(matches) != 1 or matches[0].get("digest", "").split(":")[-1] != DIGEST:
        raise RuntimeError("STOP_LOCAL_MODEL_DIGEST_MISMATCH")
    return matches[0]


def post_chat(request, image_bytes):
    body = {
        "model": MODEL,
        "stream": False,
        "format": request["answer_schema"],
        "messages": [{"role": "user", "content": request["prompt"],
                      "images": [base64.b64encode(image_bytes).decode("ascii")]}],
        "options": request["options"],
        "keep_alive": "5m",
    }
    encoded = json.dumps(body, separators=(",", ":")).encode()
    req = urllib.request.Request(ENDPOINT + "/api/chat", data=encoded,
                                 headers={"Content-Type": "application/json"})
    started = time.monotonic_ns()
    with urllib.request.urlopen(req, timeout=240) as response:
        result = json.loads(response.read())
    elapsed = time.monotonic_ns() - started
    return result, elapsed, sha(encoded)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("exchange", type=Path)
    parser.add_argument("images", type=Path)
    parser.add_argument("--mock", action="store_true", help="construction only; never formal")
    parser.add_argument("--max-calls", type=int, default=9)
    args = parser.parse_args()
    if args.max_calls != 9:
        raise SystemExit("STOP_CALL_BUDGET_MISMATCH")
    initial = None if args.mock else check_model()
    seen = set()
    receipts = []
    while True:
        requests = sorted(args.exchange.glob("request-*.json"))
        pending = [p for p in requests if p.stem not in seen]
        for path in pending:
            request = json.loads(path.read_text())
            call_id = request["call_id"]
            if call_id in seen or len(seen) >= args.max_calls:
                raise SystemExit("STOP_DUPLICATE_OR_EXCESS_CALL")
            if request.get("model") != MODEL or request.get("model_digest") != DIGEST:
                raise SystemExit("STOP_REQUEST_MODEL_IDENTITY_MISMATCH")
            image_path = args.images / request["image_path"]
            image_bytes = image_path.read_bytes()
            if sha(image_bytes) != request.get("image_sha256"):
                raise SystemExit("STOP_REQUEST_IMAGE_HASH_MISMATCH")
            if args.mock:
                response = {"status": "MOCK_CONSTRUCTION_ONLY", "ollama_response": {
                    "message": {"content": "{\"answer\":\"READY\"}"},
                    "prompt_eval_count": 0, "eval_count": 0,
                    "total_duration": 0, "load_duration": 0,
                    "prompt_eval_duration": 0, "eval_duration": 0,
                }, "model_digest": "MOCK", "elapsed_ns": 0, "request_body_sha256": "MOCK"}
            else:
                current = check_model()
                result, elapsed, body_sha = post_chat(request, image_bytes)
                if result.get("model") != MODEL:
                    raise SystemExit("STOP_RESPONSE_MODEL_NAME_MISMATCH")
                response = {"status": "OK", "ollama_response": result,
                            "model_digest": current["digest"].split(":")[-1],
                            "elapsed_ns": elapsed, "request_body_sha256": body_sha}
            (args.exchange / f"response-{call_id}.json").write_text(json.dumps(response, sort_keys=True) + "\n")
            seen.add(path.stem)
            receipts.append({"call_id": call_id, "request_sha256": sha(path.read_bytes()),
                             "response_sha256": sha((args.exchange / f"response-{call_id}.json").read_bytes()),
                             "elapsed_ns": response["elapsed_ns"]})
            print(json.dumps({"call_id": call_id, "status": response["status"],
                              "calls_completed": len(seen)}, sort_keys=True), flush=True)
        if (args.exchange / "DONE").exists():
            break
        time.sleep(0.05)
    if not args.mock:
        final = check_model()
        if final["digest"].split(":")[-1] != DIGEST:
            raise SystemExit("STOP_FINAL_MODEL_DIGEST_MISMATCH")
    (args.exchange / "BRIDGE_SUMMARY.json").write_text(json.dumps({
        "mode": "MOCK_CONSTRUCTION_ONLY" if args.mock else "LOCAL_OLLAMA",
        "model": MODEL, "digest": DIGEST, "calls": len(seen),
        "initial_model": initial, "receipts": receipts,
    }, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()

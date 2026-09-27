"""One-shot loopback Ollama bridge; preserves successful and failed HTTP bytes."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

ENDPOINT = "http://127.0.0.1:11434"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def get_json(path):
    with urllib.request.urlopen(ENDPOINT + path, timeout=10) as response:
        return json.loads(response.read())


def check_model(freeze):
    rows = get_json("/api/tags")["models"]
    matches = [r for r in rows if r.get("name") == freeze["model"]]
    if len(matches) != 1 or matches[0].get("digest", "").split(":")[-1] != freeze["model_digest"]:
        raise RuntimeError("STOP_LOCAL_MODEL_DIGEST_MISMATCH")
    return matches[0]


def save_response(path, result):
    raw = result.pop("raw_body", b"")
    request_body = result.pop("request_body", b"")
    result["raw_body_base64"] = base64.b64encode(raw).decode("ascii")
    result["raw_body_sha256"] = sha(raw)
    result["request_body_base64"] = base64.b64encode(request_body).decode("ascii")
    result["request_body_sha256"] = sha(request_body)
    path.write_text(json.dumps(result, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("exchange", type=Path)
    parser.add_argument("images", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    freeze = json.loads((Path(__file__).resolve().parent / "FREEZE.json").read_text())
    initial = None if args.mock else check_model(freeze)
    seen, receipts, stop, submitted = set(), [], None, 0
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        paths = sorted(args.exchange.glob("request-*.json"))
        pending = [p for p in paths if p.name not in seen]
        for path in pending:
            request_bytes = path.read_bytes()
            request = json.loads(request_bytes)
            call_id = request["call_id"]
            response_path = args.exchange / f"response-{call_id}.json"
            try:
                if call_id in seen or len(seen) >= 9:
                    raise RuntimeError("STOP_DUPLICATE_OR_EXCESS_CALL")
                if request.get("model") != freeze["model"] or request.get("model_digest") != freeze["model_digest"] or request.get("format") != "json":
                    raise RuntimeError("STOP_REQUEST_CONTRACT_MISMATCH")
                image = base64.b64decode(request["image_png_base64"], validate=True)
                if sha(image) != request.get("image_sha256"):
                    raise RuntimeError("STOP_REQUEST_IMAGE_HASH_MISMATCH")
                if args.mock:
                    response = {"status": "MOCK_CONSTRUCTION_ONLY", "http_status": 200, "http_headers": {},
                                "ollama_response": {"model": freeze["model"], "message": {"content": '{"answer":"READY"}'},
                                                    "prompt_eval_count": 0, "eval_count": 0},
                                "model_digest": freeze["model_digest"], "elapsed_ns": 0, "raw_body": b"mock"}
                else:
                    current = check_model(freeze)
                    payload = json.dumps({"model": freeze["model"], "messages": [{"role": "user", "content": request["prompt"],
                                          "images": [request["image_png_base64"]]}], "stream": False, "format": "json",
                                          "options": request["options"], "keep_alive": "5m"}, separators=(",", ":")).encode()
                    http_request = urllib.request.Request(ENDPOINT + "/api/chat", data=payload,
                                                          headers={"Content-Type": "application/json"})
                    started = time.monotonic_ns()
                    submitted += 1
                    try:
                        with urllib.request.urlopen(http_request, timeout=240) as res:
                            body, status, headers = res.read(), res.status, dict(res.headers.items())
                        transport = "OK"
                    except urllib.error.HTTPError as exc:
                        body, status = exc.read(), exc.code
                        headers = dict(exc.headers.items()) if exc.headers else {}
                        transport = "HTTP_ERROR"
                    elapsed = time.monotonic_ns() - started
                    try:
                        parsed = json.loads(body)
                    except Exception:
                        parsed = None
                    after = check_model(freeze)
                    response = {"status": transport, "http_status": status, "http_headers": headers,
                                "ollama_response": parsed, "model_digest": after.get("digest", "").split(":")[-1],
                                "elapsed_ns": elapsed, "request_body_sha256": sha(payload), "request_body": payload, "raw_body": body}
                    if transport != "OK":
                        stop = "STOP_HTTP_ERROR"
                save_response(response_path, response)
            except Exception as exc:
                msg = f"{type(exc).__name__}:{exc}".encode()
                save_response(response_path, {"status": "STOP_BRIDGE_ERROR", "http_status": None, "http_headers": {},
                                              "ollama_response": None, "model_digest": "", "elapsed_ns": None,
                                              "raw_body": msg})
                stop = "STOP_BRIDGE_ERROR"
            seen.add(path.name)
            receipts.append({"call_id": call_id, "request_sha256": sha(request_bytes),
                             "response_sha256": sha(response_path.read_bytes()),
                             "http_status": json.loads(response_path.read_text()).get("http_status")})
            print(json.dumps({"call_id": call_id, "submitted": not args.mock, "status": json.loads(response_path.read_text())["status"],
                              "completed_calls": len(seen)}, sort_keys=True), flush=True)
        if (args.exchange / "DONE").exists() and len(seen) == len(list(args.exchange.glob("request-*.json"))):
            break
        time.sleep(0.05)
    if not (args.exchange / "DONE").exists():
        stop = stop or "STOP_BRIDGE_TIMEOUT"
    final = None if args.mock else check_model(freeze)
    (args.output / "BRIDGE_SUMMARY.json").write_text(json.dumps({"mode": "MOCK_CONSTRUCTION_ONLY" if args.mock else "LOCAL_OLLAMA",
        "model": freeze["model"], "digest": freeze["model_digest"], "calls_submitted": submitted,
        "responses_written": len(seen), "initial_model_digest": "MOCK" if args.mock else initial["digest"].split(":")[-1],
        "final_model_digest": "MOCK" if args.mock else final["digest"].split(":")[-1], "stop": stop,
        "receipts": receipts}, indent=2, sort_keys=True) + "\n")
    if stop and not args.mock:
        print(json.dumps({"bridge_stop": stop, "responses_written": len(seen)}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

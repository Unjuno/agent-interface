"""One-shot loopback bridge that preserves full HTTPError responses."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

MODEL = "qwen2.5vl:7b"
DIGEST = "5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc"
ENDPOINT = "http://127.0.0.1:11434"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def get_json(path):
    with urllib.request.urlopen(ENDPOINT + path, timeout=10) as response:
        return json.loads(response.read())


def verify_model():
    rows = get_json("/api/tags")["models"]
    matches = [row for row in rows if row.get("name") == MODEL]
    if len(matches) != 1 or matches[0].get("digest", "").split(":")[-1] != DIGEST:
        raise RuntimeError("STOP_LOCAL_MODEL_DIGEST_MISMATCH")
    return matches[0]


def save_response(path, result):
    body = result.pop("body", b"")
    result["body_base64"] = base64.b64encode(body).decode("ascii")
    result["body_sha256"] = sha(body)
    path.write_text(json.dumps(result, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("exchange", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    request_path = args.exchange / "request-01.json"
    deadline = time.monotonic() + 180
    while not request_path.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not request_path.exists():
        raise SystemExit("STOP_REQUEST_NOT_CREATED")
    request_bytes = request_path.read_bytes()
    request = json.loads(request_bytes)
    if request.get("model") != MODEL or request.get("model_digest") != DIGEST or request.get("format") != "json":
        raise SystemExit("STOP_FROZEN_REQUEST_MISMATCH")
    if args.mock:
        response = {"transport_status": "OK", "http_status": 200,
                    "body": json.dumps({"message": {"content": "{\"answer\":\"READY\"}"},
                                        "model": MODEL, "done": True}).encode(),
                    "elapsed_ns": 0, "model_digest": DIGEST, "mode": "MOCK_CONSTRUCTION"}
    else:
        submitted = 0
        model_before_digest = ""
        try:
            model_before = verify_model()
            model_before_digest = model_before.get("digest", "").split(":")[-1]
            body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": request["prompt"],
                              "images": [request["image_png_base64"]]}], "stream": False,
                              "format": "json", "options": request["options"],
                              "keep_alive": request["keep_alive"]}, separators=(",", ":")).encode()
            req = urllib.request.Request(ENDPOINT + "/api/chat", data=body,
                                         headers={"Content-Type": "application/json"})
            started = time.monotonic_ns()
            submitted = 1
            try:
                with urllib.request.urlopen(req, timeout=180) as http_response:
                    result_body = http_response.read()
                    status = http_response.status
                    headers = dict(http_response.headers.items())
                transport = "OK"
            except urllib.error.HTTPError as exc:
                result_body = exc.read()
                status = exc.code
                headers = dict(exc.headers.items()) if exc.headers else {}
                transport = "HTTP_ERROR"
            elapsed = time.monotonic_ns() - started
            try:
                model_after_digest = verify_model().get("digest", "").split(":")[-1]
                identity_check = "OK" if model_after_digest == DIGEST else "MISMATCH"
            except Exception as exc:
                model_after_digest = ""
                identity_check = f"POSTCHECK_ERROR:{type(exc).__name__}:{exc}"
            response = {"transport_status": transport, "http_status": status,
                        "http_headers": headers, "body": result_body, "elapsed_ns": elapsed,
                        "model_digest": model_after_digest, "model_before_digest": model_before_digest,
                        "identity_check": identity_check, "mode": "LOCAL_OLLAMA"}
        except Exception as exc:
            error_body = f"{type(exc).__name__}:{exc}".encode()
            response = {"transport_status": "BRIDGE_ERROR", "http_status": None,
                        "http_headers": {}, "body": error_body, "elapsed_ns": None,
                        "model_digest": "", "model_before_digest": model_before_digest,
                        "identity_check": "NOT_COMPLETED", "mode": "LOCAL_OLLAMA",
                        "calls_submitted": submitted}
    response_path = args.exchange / "response-01.json"
    save_response(response_path, response)
    summary = {"mode": response["mode"], "request_sha256": sha(request_bytes),
               "response_sha256": sha(response_path.read_bytes()), "http_status": response["http_status"],
               "transport_status": response["transport_status"], "elapsed_ns": response.get("elapsed_ns"),
               "calls_submitted": 0 if args.mock else response.get("calls_submitted", 1)}
    (args.output / "BRIDGE_SUMMARY.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("mode", "http_status", "transport_status", "calls_submitted")}, sort_keys=True), flush=True)
    while not (args.exchange / "DONE").exists() and time.monotonic() < deadline:
        time.sleep(0.05)


if __name__ == "__main__":
    main()

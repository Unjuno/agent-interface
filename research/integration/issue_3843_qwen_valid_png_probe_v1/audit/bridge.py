"""Single-request loopback Ollama bridge preserving exact HTTP errors."""
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


def api(path):
    with urllib.request.urlopen(ENDPOINT + path, timeout=10) as response:
        return json.loads(response.read())


def save(path, response):
    body = response.pop("body", b"")
    response["body_base64"] = base64.b64encode(body).decode("ascii")
    response["body_sha256"] = sha(body)
    path.write_text(json.dumps(response, sort_keys=True) + "\n")


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
    if request.get("format") != "json" or request.get("call_id") != "01":
        raise SystemExit("STOP_REQUEST_CONTRACT_MISMATCH")
    started = time.monotonic_ns()
    if args.mock:
        response = {"transport_status": "OK", "http_status": 200, "model_digest": request["model_digest"],
                    "mode": "MOCK_CONSTRUCTION", "body": json.dumps({"model": request["model"], "done": True,
                    "message": {"content": "{\"answer\":\"READY\"}"}}).encode(), "elapsed_ns": 0}
    else:
        submitted = 0
        before_digest = ""
        try:
            tags = api("/api/tags")["models"]
            matches = [item for item in tags if item.get("name") == request["model"]]
            if len(matches) != 1 or matches[0].get("digest", "").split(":")[-1] != request["model_digest"]:
                raise RuntimeError("STOP_MODEL_DIGEST_MISMATCH")
            before_digest = matches[0]["digest"].split(":")[-1]
            payload = json.dumps({"model": request["model"], "messages": [{"role": "user",
                                  "content": request["prompt"], "images": [request["image_png_base64"]]}],
                                  "stream": False, "format": "json", "options": request["options"],
                                  "keep_alive": request["keep_alive"]}, separators=(",", ":")).encode()
            http_request = urllib.request.Request(ENDPOINT + "/api/chat", data=payload,
                                                  headers={"Content-Type": "application/json"})
            submitted = 1
            try:
                with urllib.request.urlopen(http_request, timeout=180) as res:
                    body, status, headers = res.read(), res.status, dict(res.headers.items())
                transport = "OK"
            except urllib.error.HTTPError as exc:
                body, status = exc.read(), exc.code
                headers = dict(exc.headers.items()) if exc.headers else {}
                transport = "HTTP_ERROR"
            elapsed = time.monotonic_ns() - started
            after = api("/api/tags")["models"]
            after = [item for item in after if item.get("name") == request["model"]]
            after_digest = after[0].get("digest", "").split(":")[-1] if len(after) == 1 else ""
            response = {"transport_status": transport, "http_status": status, "http_headers": headers,
                        "body": body, "elapsed_ns": elapsed, "model_digest": after_digest,
                        "model_before_digest": before_digest, "identity_check": "OK" if after_digest == request["model_digest"] else "MISMATCH",
                        "calls_submitted": submitted, "mode": "LOCAL_OLLAMA"}
        except Exception as exc:
            body = f"{type(exc).__name__}:{exc}".encode()
            response = {"transport_status": "BRIDGE_ERROR", "http_status": None, "http_headers": {},
                        "body": body, "elapsed_ns": None, "model_digest": "", "model_before_digest": before_digest,
                        "identity_check": "NOT_COMPLETED", "calls_submitted": submitted, "mode": "LOCAL_OLLAMA"}
    response_path = args.exchange / "response-01.json"
    save(response_path, response)
    summary = {"mode": response["mode"], "request_sha256": sha(request_bytes),
               "response_sha256": sha(response_path.read_bytes()), "http_status": response["http_status"],
               "transport_status": response["transport_status"], "elapsed_ns": response.get("elapsed_ns"),
               "calls_submitted": response.get("calls_submitted", 0 if args.mock else 1)}
    (args.output / "BRIDGE_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)
    while not (args.exchange / "DONE").exists() and time.monotonic() < deadline:
        time.sleep(0.05)


if __name__ == "__main__":
    main()

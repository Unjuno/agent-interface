import argparse
import base64
import json
import os
import struct
import subprocess
import tempfile
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def chunk(kind, data):
    return (struct.pack("!I", len(data)) + kind + data +
            struct.pack("!I", zlib.crc32(kind + data) & 0xffffffff))


def png_rgb_2x2():
    raw = b"\x00" + bytes((10, 20, 30)) * 2 + b"\x00" + bytes((40, 50, 60)) * 2
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack("!2I5B", 2, 2, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def sse(*events):
    return "".join("event: " + item["type"] + "\ndata: " +
                   json.dumps(item, separators=(",", ":")) + "\n\n"
                   for item in events).encode()


def created(response_id):
    return {"type": "response.created", "response": {"id": response_id}}


def message(response_id, text):
    return {"type": "response.output_item.done", "item": {
        "type": "message", "role": "assistant", "id": "msg-" + response_id,
        "content": [{"type": "output_text", "text": text}]}}


def completed(response_id):
    return {"type": "response.completed", "response": {
        "id": response_id, "usage": {"input_tokens": 3, "output_tokens": 2,
                                       "total_tokens": 5}}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="new, empty directory for A01 receipts")
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)

    requests, lock = [], threading.Lock()
    first_open = threading.Event()
    release_first = threading.Event()
    second_seen = threading.Event()
    timing, first_write_errors = {}, []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_args):
            pass

        def do_GET(self):
            if self.path.endswith("/models"):
                body = json.dumps({"object": "list", "data": [{
                    "id": "mock-model", "object": "model", "created": 0,
                    "owned_by": "openai"}]}).encode()
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404)

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("content-length", "0")))
            with lock:
                index = len(requests)
                requests.append({"at": time.monotonic(), "path": self.path,
                                 "client_address": list(self.client_address),
                                 "body": json.loads(body)})
            if not self.path.endswith("/responses"):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("connection", "close")
            self.end_headers()
            response_id = f"a01-mock-response-{index + 1}"
            try:
                self.wfile.write(sse(created(response_id)))
                self.wfile.flush()
                if index == 0:
                    first_open.set()
                    release_first.wait(8)
                    timing["first_response_released_at"] = time.monotonic()
                    self.wfile.write(sse(message(response_id, '{"kind":"stale"}'),
                                          completed(response_id)))
                    self.wfile.flush()
                else:
                    timing["second_request_at"] = time.monotonic()
                    second_seen.set()
                    self.wfile.write(sse(message(response_id, '{"kind":"fresh"}'),
                                          completed(response_id)))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError) as error:
                if index == 0:
                    first_write_errors.append(type(error).__name__)
            finally:
                self.close_connection = True

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    process = None
    result = None
    try:
        version = subprocess.run(["/opt/homebrew/bin/codex", "--version"], capture_output=True,
                                 text=True, timeout=3).stdout.strip()
        if version != "codex-cli 0.146.1":
            raise RuntimeError(f"expected codex-cli 0.146.1, found {version!r}")

        # Keep generated CODEX_HOME state out of the repository package.
        scratch = Path(tempfile.mkdtemp(prefix="codex-interrupt-a01-"))
        home, cwd, tmp = scratch / "home", scratch / "cwd", scratch / "tmp"
        home.mkdir()
        cwd.mkdir()
        tmp.mkdir()
        (home / "config.toml").write_text(
            'model = "mock-model"\napproval_policy = "never"\n'
            'sandbox_mode = "read-only"\nmodel_provider = "mock_provider"\n'
            '[model_providers.mock_provider]\nname = "local mock"\n'
            f'base_url = "http://127.0.0.1:{server.server_port}/v1"\n'
            'wire_api = "responses"\nrequest_max_retries = 0\n'
            'stream_max_retries = 0\n'
            '[analytics]\nenabled = false\n', encoding="utf-8")
        # Do not pass user tokens, proxies, or unrelated settings into the probe.
        env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
               "HOME": str(home), "CODEX_HOME": str(home), "TMPDIR": str(tmp),
               "CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG": "1",
               "RUST_LOG": "warn", "LANG": "en_US.UTF-8"}
        process = subprocess.Popen(["/opt/homebrew/bin/codex", "app-server", "--stdio"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1, env=env, cwd=str(cwd))
        rows, rows_lock = [], threading.Lock()

        def read_stdout():
            for line in process.stdout:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                with rows_lock:
                    rows.append((time.monotonic(), row))

        threading.Thread(target=read_stdout, daemon=True).start()
        write_lock, next_id = threading.Lock(), 0

        def send(method, params):
            nonlocal next_id
            next_id += 1
            request_id = next_id
            with write_lock:
                process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id,
                                                "method": method, "params": params}) + "\n")
                process.stdin.flush()
            return request_id

        def wait_response(request_id, timeout=6):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                with rows_lock:
                    for _, row in rows:
                        if row.get("id") == request_id:
                            return row
                if process.poll() is not None:
                    break
                time.sleep(.01)
            raise TimeoutError(f"missing JSON-RPC response {request_id}")

        def wait_completion(thread_id, turn_id, timeout=6):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                with rows_lock:
                    for _, row in rows:
                        if (row.get("method") == "turn/completed" and
                            row.get("params", {}).get("threadId") == thread_id and
                            row.get("params", {}).get("turn", {}).get("id") == turn_id):
                            return row["params"]["turn"]
                if process.poll() is not None:
                    break
                time.sleep(.01)
            raise TimeoutError(f"missing turn/completed for {turn_id}")

        wait_response(send("initialize", {"clientInfo": {"name": "a01",
            "title": "A01", "version": "1"}, "capabilities": {
            "experimentalApi": False, "requestAttestation": False}}))
        with write_lock:
            process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "initialized",
                                            "params": {}}) + "\n")
            process.stdin.flush()
        thread_response = wait_response(send("thread/start", {"model": "mock-model",
            "cwd": str(cwd), "approvalPolicy": "never", "sandbox": "read-only",
            "baseInstructions": "Use only the supplied current observation.",
            "ephemeral": True, "threadSource": "exec"}))
        thread_id = thread_response["result"]["thread"]["id"]
        first = wait_response(send("turn/start", {"threadId": thread_id,
            "input": [{"type": "text", "text": "Initial request",
                       "text_elements": []}], "model": "mock-model", "effort": "low",
            "outputSchema": {"type": "object", "properties": {
                "kind": {"type": "string"}}, "required": ["kind"],
                "additionalProperties": False}}))
        first_turn_id = first["result"]["turn"]["id"]
        if not first_open.wait(6):
            raise TimeoutError("first mock Responses request did not arrive")

        interrupt = wait_response(send("turn/interrupt", {
            "threadId": thread_id, "turnId": first_turn_id}), timeout=4)
        if "error" in interrupt:
            raise RuntimeError("turn/interrupt rejected: " + json.dumps(interrupt))
        first_turn = wait_completion(thread_id, first_turn_id)

        image_b64 = base64.b64encode(png_rgb_2x2()).decode("ascii")
        fresh = wait_response(send("turn/start", {"threadId": thread_id,
            "input": [{"type": "text",
                "text": "UNTRUSTED CURRENT OBSERVATION: ammo=37",
                "text_elements": []}, {"type": "image",
                "url": "data:image/png;base64," + image_b64,
                "detail": "auto"}], "model": "mock-model", "effort": "low",
            "outputSchema": {"type": "object", "properties": {
                "kind": {"type": "string"}}, "required": ["kind"],
                "additionalProperties": False}}), timeout=4)
        second_turn_id = fresh.get("result", {}).get("turn", {}).get("id")
        if not second_turn_id:
            raise RuntimeError("fresh turn rejected: " + json.dumps(fresh))
        second_seen_before_release = second_seen.wait(4)
        release_first.set()
        second_turn = wait_completion(thread_id, second_turn_id)
        with lock:
            captured = list(requests)
        second_request = captured[1] if len(captured) > 1 else None
        second_body = json.dumps(second_request["body"]) if second_request else ""
        result = {
            "disposition": "PASS_INTERRUPT_ADMITS_FRESH_OBSERVATION_BEFORE_HELD_RESPONSE_RELEASE"
                if (first_turn.get("status") == "interrupted" and second_turn_id and
                    second_seen_before_release and second_turn.get("status") == "completed" and
                    len(captured) == 2 and
                    "UNTRUSTED CURRENT OBSERVATION: ammo=37" in second_body and
                    image_b64 in second_body) else "FAIL_OR_INCOMPLETE",
            "app_server_version": version,
            "requests_to_loopback_mock_only": len(captured),
            "thread_id": thread_id,
            "first_turn_id": first_turn_id,
            "first_turn_status": first_turn.get("status"),
            "second_turn_thread_id": thread_id,
            "second_turn_id": second_turn_id,
            "same_thread": bool(second_turn_id and thread_id),
            "second_turn_status": second_turn.get("status"),
            "second_request_before_first_response_release": second_seen_before_release,
            "second_request_contains_observation_text":
                "UNTRUSTED CURRENT OBSERVATION: ammo=37" in second_body,
            "second_request_contains_valid_png": bool(image_b64 and image_b64 in second_body),
            "first_response_released_at": timing.get("first_response_released_at"),
            "second_request_at": timing.get("second_request_at"),
            "first_stream_write_errors_after_release": first_write_errors,
        }
    except Exception as error:
        result = {"disposition": "HOLD_HARNESS_ERROR", "error_type": type(error).__name__,
                  "error": str(error)}
    finally:
        release_first.set()
        if process is not None:
            try:
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
            except OSError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            result["app_server_exit_code"] = process.returncode
        with lock:
            result.setdefault("requests_to_loopback_mock_only", len(requests))
            (out / "requests.json").write_text(
                json.dumps(requests, indent=2) + "\n", encoding="utf-8")
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                         encoding="utf-8")
        (out / "process_exit.txt").write_text(
            (str(process.returncode) if process is not None else "not-started") + "\n",
            encoding="ascii")
        server.shutdown()
        server.server_close()

    print(json.dumps(result, indent=2))
    exit_code = 0 if result["disposition"] == "PASS_INTERRUPT_ADMITS_FRESH_OBSERVATION_BEFORE_HELD_RESPONSE_RELEASE" else 1
    (out / "runner_exit.txt").write_text(str(exit_code) + "\n", encoding="ascii")
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()


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


def png_chunk(kind, data):
    return (struct.pack("!I", len(data)) + kind + data +
            struct.pack("!I", zlib.crc32(kind + data) & 0xffffffff))


def png_rgb_2x2():
    raw = b"\x00" + bytes((10, 20, 30)) * 2 + b"\x00" + bytes((40, 50, 60)) * 2
    return (b"\x89PNG\r\n\x1a\n" +
            png_chunk(b"IHDR", struct.pack("!2I5B", 2, 2, 8, 2, 0, 0, 0)) +
            png_chunk(b"IDAT", zlib.compress(raw)) + png_chunk(b"IEND", b""))


def event_stream(*events):
    return "".join("event: " + event["type"] + "\ndata: " +
                   json.dumps(event, separators=(",", ":")) + "\n\n"
                   for event in events).encode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="new, empty directory for this replay's receipts")
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)

    calls, lock = [], threading.Lock()
    first_open = threading.Event()
    release_first = threading.Event()
    second_seen = threading.Event()
    timing, transport_errors = {}, []

    def response_created(response_id):
        return {"type": "response.created", "response": {"id": response_id}}

    def assistant_message(response_id, text):
        return {"type": "response.output_item.done", "item": {
            "type": "message", "role": "assistant", "id": "msg-" + response_id,
            "content": [{"type": "output_text", "text": text}]}}

    def response_completed(response_id):
        return {"type": "response.completed", "response": {"id": response_id,
            "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}}}

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
                index = len(calls)
                calls.append({"at": time.monotonic(), "body": json.loads(body)})
            if not self.path.endswith("/responses"):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("connection", "close")
            self.end_headers()
            response_id = f"mock-response-{index + 1}"
            try:
                self.wfile.write(event_stream(response_created(response_id)))
                self.wfile.flush()
                if index == 0:
                    first_open.set()
                    release_first.wait(8)
                    timing["first_response_completed_at"] = time.monotonic()
                    text = '{"kind":"first"}'
                else:
                    timing["followup_request_started_at"] = time.monotonic()
                    second_seen.set()
                    text = '{"kind":"observation_received"}'
                self.wfile.write(event_stream(assistant_message(response_id, text),
                                              response_completed(response_id)))
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError) as error:
                transport_errors.append(type(error).__name__)
            finally:
                self.close_connection = True

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    process = None
    try:
        version = subprocess.run(["codex.exe", "--version"], capture_output=True,
                                 text=True, timeout=3).stdout.strip()
        if version != "codex-cli 0.160.0":
            raise RuntimeError(f"expected codex-cli 0.160.0, found {version!r}")
        # Preserve this isolated home rather than deleting it while App Server
        # (or a child still flushing local state) may retain Windows handles.
        scratch = Path(tempfile.mkdtemp(prefix="codex-active-turn-a04-"))
        home, cwd = scratch / "home", scratch / "cwd"
        home.mkdir()
        cwd.mkdir()
        (home / "config.toml").write_text(
            f'model = "mock-model"\napproval_policy = "never"\n'
            f'sandbox_mode = "read-only"\nmodel_provider = "mock_provider"\n'
            f'[model_providers.mock_provider]\nname = "local mock"\n'
            f'base_url = "http://127.0.0.1:{server.server_port}/v1"\n'
            'wire_api = "responses"\nrequest_max_retries = 0\n'
            'stream_max_retries = 0\n', encoding="utf-8")
        env = os.environ.copy()
        env.update(CODEX_HOME=str(home), CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG="1",
                   RUST_LOG="warn")
        process = subprocess.Popen(["codex.exe", "app-server", "--stdio"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1, env=env, cwd=str(cwd))
        messages, output_lock = [], threading.Lock()

        def read_output():
            for line in process.stdout:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                with output_lock:
                    messages.append((time.monotonic(), row))

        threading.Thread(target=read_output, daemon=True).start()
        send_lock, request_id = threading.Lock(), 0

        def send(method, params):
            nonlocal request_id
            request_id += 1
            current_id = request_id
            with send_lock:
                process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": current_id,
                                                "method": method, "params": params}) + "\n")
                process.stdin.flush()
            return current_id

        def wait_response(current_id, timeout=6):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                with output_lock:
                    for _, row in messages:
                        if row.get("id") == current_id:
                            return row
                if process.poll() is not None:
                    break
                time.sleep(.01)
            raise TimeoutError(f"missing JSON-RPC response {current_id}")

        wait_response(send("initialize", {"clientInfo": {"name": "a04",
            "title": "a04", "version": "1"}, "capabilities": {
            "experimentalApi": False, "requestAttestation": False}}))
        with send_lock:
            process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "initialized",
                                            "params": {}}) + "\n")
            process.stdin.flush()
        thread_response = wait_response(send("thread/start", {"model": "mock-model",
            "cwd": str(cwd), "approvalPolicy": "never", "sandbox": "read-only",
            "baseInstructions": "Use supplied context.", "ephemeral": True,
            "threadSource": "exec"}))
        thread_id = thread_response["result"]["thread"]["id"]
        first = wait_response(send("turn/start", {"threadId": thread_id,
            "input": [{"type": "text", "text": "Initial request", "text_elements": []}],
            "model": "mock-model", "effort": "low", "outputSchema": {
                "type": "object", "properties": {"kind": {"type": "string"}},
                "required": ["kind"], "additionalProperties": False}}))
        turn_id = first["result"]["turn"]["id"]
        if not first_open.wait(6):
            raise TimeoutError("first mock Responses request did not arrive")
        tool_output_sent_at = time.monotonic()
        image_b64 = base64.b64encode(png_rgb_2x2()).decode("ascii")
        steering = wait_response(send("turn/start", {"threadId": thread_id, "input": [],
            "toolOutput": {"name": "live_observation", "namespace": "agent-interface",
                "output": [{"type": "input_text",
                    "text": "UNTRUSTED CURRENT OBSERVATION: ammo=37"},
                    {"type": "input_image", "image_url":
                     "data:image/png;base64," + image_b64, "detail": "auto"}]}}), timeout=4)
        if "error" in steering:
            raise RuntimeError("active-turn toolOutput rejected: " + json.dumps(steering))
        steering_turn_id = steering.get("result", {}).get("turn", {}).get("id")
        followup_before_release = second_seen.wait(1.5)
        if not followup_before_release:
            release_first.set()
            second_seen.wait(6)
        release_first.set()
        deadline = time.monotonic() + 8
        completed = []
        while time.monotonic() < deadline:
            with output_lock:
                completed = [row for _, row in messages
                    if row.get("method") == "turn/completed" and
                    row.get("params", {}).get("threadId") == thread_id and
                    row.get("params", {}).get("turn", {}).get("id") == turn_id]
            if completed or process.poll() is not None:
                break
            time.sleep(.02)
        with lock:
            captured = list(calls)
        followup = captured[1] if len(captured) > 1 else None
        followup_json = json.dumps(followup["body"]) if followup else ""
        result = {"disposition": "PASS_SAME_TURN_OBSERVATION_QUEUED_AFTER_CURRENT_INFERENCE"
                if followup and steering_turn_id == turn_id else "FAIL_OR_INCOMPLETE",
            "app_server_version": version, "requests_to_loopback_mock_only": len(captured),
            "initial_turn_id": turn_id, "steering_response_turn_id": steering_turn_id,
            "same_turn": steering_turn_id == turn_id,
            "tool_output_text_present_in_followup_request":
                "UNTRUSTED CURRENT OBSERVATION: ammo=37" in followup_json,
            "valid_png_b64_present_in_followup_request": bool(image_b64 and image_b64 in followup_json),
            "followup_request_after_first_response_completed": bool(followup and
                timing.get("first_response_completed_at") and
                followup["at"] >= timing["first_response_completed_at"]),
            "seconds_from_tool_output_send_to_first_response_completion":
                round(timing["first_response_completed_at"] - tool_output_sent_at, 3)
                if timing.get("first_response_completed_at") else None,
            "followup_request_ms_after_first_response_completion": round(
                (followup["at"] - timing["first_response_completed_at"]) * 1000, 3)
                if followup and timing.get("first_response_completed_at") else None,
            "terminal_status": completed[0]["params"]["turn"].get("status") if completed else None,
            "mock_transport_errors": transport_errors}
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        with (out / "process_exit.txt").open("w", encoding="ascii") as receipt:
            receipt.write("pending\n")
        process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        (out / "process_exit.txt").write_text(str(process.returncode) + "\n", encoding="ascii")
    finally:
        release_first.set()
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=3)
        server.shutdown()
        server.server_close()

    print(json.dumps(result, indent=2))
    if result["disposition"] != "PASS_SAME_TURN_OBSERVATION_QUEUED_AFTER_CURRENT_INFERENCE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()


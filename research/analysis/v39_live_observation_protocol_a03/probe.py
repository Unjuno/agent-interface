"""Measure whether ExternalMessage advances a model request before its predecessor responds.

The App Server uses a loopback-only mock Responses endpoint. No model service or
game process is contacted. The first HTTP model request is held behind an event
while an ExternalMessage is sent to the active turn.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import queue
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any


EXPECTED_CLI_VERSION = "codex-cli 0.160.0"
EVENT_TEXT = "Fresh observation seq=200; HUD health 51, ammo 38."
FRAME_SHA256 = "0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c"
MOCK_TEXT = "mock final"
INITIAL_PENDING_WINDOW_S = 2.0
PROTOCOL_TIMEOUT_S = 20.0


def classify_request_order(second_request_ns, first_response_completed_ns):
    """Classify whether ExternalMessage led to a request before the first ended."""
    if second_request_ns is None:
        return "SECOND_REQUEST_NOT_OBSERVED"
    if (type(second_request_ns) is not int or second_request_ns < 1 or
            type(first_response_completed_ns) is not int or
            first_response_completed_ns < 1):
        return "ORDER_UNVERIFIABLE"
    if second_request_ns < first_response_completed_ns:
        return "SECOND_REQUEST_WHILE_INITIAL_PENDING"
    return "SECOND_REQUEST_AFTER_INITIAL_COMPLETION"


def turn_id_from_start_reply(reply):
    """Extract the actual turn ID returned by an App Server turn/start RPC."""
    if type(reply) is not dict:
        return None
    result = reply.get("result")
    if type(result) is not dict:
        return None
    turn = result.get("turn")
    if type(turn) is not dict:
        return None
    identifier = turn.get("id")
    return identifier if type(identifier) is str and identifier else None


def _response_sse(index: int) -> bytes:
    response_id = f"resp_{index}"
    message_id = f"msg_{index}"
    response = {
        "id": response_id,
        "object": "response",
        "created_at": 1,
        "status": "completed",
        "model": "gpt-5.6-luna",
        "output": [{
            "id": message_id,
            "type": "message",
            "status": "completed",
            "role": "assistant",
            "content": [{"type": "output_text", "text": MOCK_TEXT, "annotations": []}],
        }],
        "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
    }
    events = [
        ("response.created", {"response": {
            key: value for key, value in response.items() if key != "output"
        } | {"status": "in_progress", "output": []}}),
        ("response.output_item.added", {"output_index": 0, "item": {
            "id": message_id, "type": "message", "status": "in_progress",
            "role": "assistant", "content": [],
        }}),
        ("response.content_part.added", {
            "item_id": message_id, "output_index": 0, "content_index": 0,
            "part": {"type": "output_text", "text": ""},
        }),
        ("response.output_text.delta", {
            "item_id": message_id, "output_index": 0, "content_index": 0,
            "delta": MOCK_TEXT,
        }),
        ("response.output_text.done", {
            "item_id": message_id, "output_index": 0, "content_index": 0,
            "text": MOCK_TEXT,
        }),
        ("response.content_part.done", {
            "item_id": message_id, "output_index": 0, "content_index": 0,
            "part": {"type": "output_text", "text": MOCK_TEXT},
        }),
        ("response.output_item.done", {"output_index": 0, "item": response["output"][0]}),
        ("response.completed", {"response": response}),
    ]
    return "".join(
        f"event: {event}\ndata: {json.dumps({'type': event, **fields})}\n\n"
        for event, fields in events
    ).encode("utf-8")


class _MockState:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.request_received_ns: list[int] = []
        self.first_request_seen = threading.Event()
        self.second_request_seen = threading.Event()
        self.release_first_response = threading.Event()
        self.first_response_release_ns: int | None = None
        self.first_response_sent_ns: int | None = None
        self.errors: list[str] = []
        self.lock = threading.Lock()


def inspect_requests(
    requests: list[dict[str, Any]], image: bytes, observation: str
) -> dict[str, Any]:
    image_data = "data:image/png;base64," + base64.b64encode(image).decode("ascii")
    function_outputs = [
        item
        for request in requests
        for item in request.get("input", [])
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    ]
    output_json = json.dumps(function_outputs, separators=(",", ":"))
    second_json = json.dumps(requests[1], separators=(",", ":")) if len(requests) > 1 else ""
    return {
        "mock_request_count": len(requests),
        "observation_text": observation,
        "text_delivered": observation in output_json,
        "image_delivered": image_data in output_json,
        "image_sha256": hashlib.sha256(image).hexdigest(),
        "image_bytes": len(image),
        "request_input_types": [
            [row.get("type") for row in request.get("input", []) if isinstance(row, dict)]
            for request in requests
        ],
        "observation_in_second_request": observation in second_json,
        "image_in_second_request": image_data in second_json,
        "input_image_count": output_json.count('"type":"input_image"'),
    }


def _run_app_server(image: bytes, pending_window_s: float) -> dict[str, Any]:
    state = _MockState()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_: Any) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802
            try:
                size = int(self.headers.get("Content-Length", "0"))
                request = json.loads(self.rfile.read(size))
                received_ns = time.monotonic_ns()
                with state.lock:
                    state.requests.append(request)
                    state.request_received_ns.append(received_ns)
                    index = len(state.requests)
                if index == 1:
                    state.first_request_seen.set()
                    if not state.release_first_response.wait(PROTOCOL_TIMEOUT_S):
                        state.errors.append("first mock response gate timed out")
                        self.send_error(504)
                        return
                elif index == 2:
                    state.second_request_seen.set()

                body = _response_sse(index)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                self.wfile.flush()
                if index == 1:
                    state.first_response_sent_ns = time.monotonic_ns()
            except Exception as exc:
                state.errors.append(f"mock handler {type(exc).__name__}: {exc}")
                try:
                    self.send_error(500)
                except OSError:
                    pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    messages: queue.Queue[dict[str, Any]] = queue.Queue()
    stderr: list[str] = []
    with tempfile.TemporaryDirectory(prefix="codex-live-observation-a02-") as home_text:
        home = Path(home_text)
        (home / "config.toml").write_text(
            f'''model = "gpt-5.6-luna"
approval_policy = "never"
sandbox_mode = "read-only"
[model_providers.mock]
name = "loopback mock"
base_url = "http://127.0.0.1:{server.server_address[1]}/v1"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
''',
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["CODEX_HOME"] = str(home)
        for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID"):
            env.pop(key, None)
        process = subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=env,
            cwd=str(home),
        )

        def read_stdout() -> None:
            assert process.stdout
            for line in process.stdout:
                try:
                    messages.put(json.loads(line))
                except json.JSONDecodeError:
                    messages.put({"_raw": line})

        def read_stderr() -> None:
            assert process.stderr
            stderr.extend(process.stderr.readlines())

        threading.Thread(target=read_stdout, daemon=True).start()
        threading.Thread(target=read_stderr, daemon=True).start()

        def send(payload: dict[str, Any]) -> None:
            assert process.stdin
            process.stdin.write(json.dumps(payload) + "\n")
            process.stdin.flush()

        def wait_for(predicate: Any, seconds: float = 12.0) -> dict[str, Any]:
            end = time.monotonic() + seconds
            observed: list[dict[str, Any]] = []
            while time.monotonic() < end:
                try:
                    message = messages.get(timeout=max(0.01, end - time.monotonic()))
                except queue.Empty:
                    break
                observed.append(message)
                if predicate(message):
                    return message
            raise TimeoutError(json.dumps(observed[-8:], default=str))

        initial_reply: dict[str, Any] = {}
        external_reply: dict[str, Any] = {}
        initial_turn_id: str | None = None
        completed: dict[str, Any] | None = None
        try:
            codex_version = subprocess.check_output(["codex", "--version"], text=True).strip()
            if codex_version != EXPECTED_CLI_VERSION:
                raise RuntimeError(f"expected {EXPECTED_CLI_VERSION}, got {codex_version}")

            send({"id": 1, "method": "initialize", "params": {
                "clientInfo": {"name": "v39-observation-a03", "title": "offline protocol ordering", "version": "1"}
            }})
            initialize_reply = wait_for(lambda message: message.get("id") == 1)
            send({"method": "initialized"})
            send({"id": 2, "method": "thread/start", "params": {
                "cwd": str(home), "model": "gpt-5.6-luna", "modelProvider": "mock",
                "approvalPolicy": "never", "sandbox": "read-only",
            }})
            thread_reply = wait_for(lambda message: message.get("id") == 2)
            if "error" in thread_reply:
                raise RuntimeError(json.dumps(thread_reply))
            thread_id = thread_reply["result"]["thread"]["id"]
            send({"id": 3, "method": "turn/start", "params": {
                "threadId": thread_id,
                "input": [{"type": "text", "text": "Say exactly INITIAL."}],
            }})
            initial_reply = wait_for(lambda message: message.get("id") == 3)
            if "error" in initial_reply:
                raise RuntimeError(json.dumps(initial_reply))
            initial_turn_id = turn_id_from_start_reply(initial_reply)
            if not initial_turn_id:
                raise RuntimeError("initial turn/start reply lacked a turn ID")
            if not state.first_request_seen.wait(12.0):
                raise TimeoutError("initial request did not reach loopback mock")

            observation = {
                "threadId": thread_id,
                "input": [],
                "toolOutput": {
                    "name": "live_observation",
                    "namespace": "agent-interface",
                    "output": [
                        {"type": "input_text", "text": EVENT_TEXT},
                        {"type": "input_image", "image_url":
                         "data:image/png;base64," + base64.b64encode(image).decode("ascii"),
                         "detail": "auto"},
                    ],
                },
            }
            send({"id": 4, "method": "turn/start", "params": observation})
            external_ack_ns = time.monotonic_ns()
            external_reply = wait_for(lambda message: message.get("id") == 4)
            external_ack_ns = time.monotonic_ns()
            if "error" in external_reply:
                raise RuntimeError(json.dumps(external_reply))

            second_before_release = state.second_request_seen.wait(pending_window_s)
            if state.second_request_seen.is_set() and len(state.request_received_ns) >= 2:
                second_request_ns = state.request_received_ns[1]
            else:
                second_request_ns = None
            state.first_response_release_ns = time.monotonic_ns()
            state.release_first_response.set()

            if not state.second_request_seen.wait(PROTOCOL_TIMEOUT_S):
                raise TimeoutError("no second model request followed ExternalMessage")
            if second_request_ns is None and len(state.request_received_ns) >= 2:
                second_request_ns = state.request_received_ns[1]

            deadline = time.monotonic() + PROTOCOL_TIMEOUT_S
            while time.monotonic() < deadline:
                try:
                    message = messages.get(timeout=0.1)
                except queue.Empty:
                    continue
                if (message.get("method") == "turn/completed" and
                        message.get("params", {}).get("turn", {}).get("id") == initial_turn_id):
                    completed = message
                    break

            external_turn_id = turn_id_from_start_reply(external_reply)
            external_status = external_reply.get("result", {}).get("turn", {}).get("status")
            inspected = inspect_requests(state.requests, image, EVENT_TEXT)
            inspected.update({
                "cli_version": codex_version,
                "loopback_only": True,
                "temporary_codex_home": True,
                "initialize_ok": "result" in initialize_reply,
                "thread_started": "result" in thread_reply,
                "external_message_accepted": "result" in external_reply,
                "initial_turn_id": initial_turn_id,
                "external_turn_id": external_turn_id,
                "external_turn_status_at_ack": external_status,
                "same_turn_id": bool(initial_turn_id and initial_turn_id == external_turn_id),
                "external_ack_ns": external_ack_ns,
                "second_request_received_ns": second_request_ns,
                "first_response_release_ns": state.first_response_release_ns,
                "first_response_sent_ns": state.first_response_sent_ns,
                "second_request_before_release_gate": second_before_release,
                "request_order": classify_request_order(
                    second_request_ns, state.first_response_sent_ns
                ),
                "turn_completed": completed is not None,
                "server_errors": list(state.errors),
                "app_server_stderr": "".join(stderr)[-2000:],
            })
            return inspected
        finally:
            state.release_first_response.set()
            if process.stdin:
                process.stdin.close()
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--pending-window-s", type=float, default=INITIAL_PENDING_WINDOW_S)
    args = parser.parse_args()
    image = args.frame.read_bytes()
    image_hash = hashlib.sha256(image).hexdigest()
    if image_hash != FRAME_SHA256:
        raise SystemExit(f"unexpected frame SHA-256: {image_hash}")
    if not (0.1 <= args.pending_window_s <= 5.0):
        raise SystemExit("pending window must be between 0.1 and 5.0 seconds")
    result = _run_app_server(image, args.pending_window_s)
    result["frame_sha256_expected"] = FRAME_SHA256
    result["frame_sequence"] = 200
    print(json.dumps(result, indent=2, sort_keys=True))
    required = (
        result["initialize_ok"] and result["thread_started"]
        and result["external_message_accepted"] and result["same_turn_id"]
        and result["external_turn_status_at_ack"] == "inProgress"
        and result["turn_completed"] and result["text_delivered"]
        and result["image_delivered"] and result["image_in_second_request"]
        and result["mock_request_count"] >= 2
        and result["first_response_sent_ns"] is not None
        and not result["server_errors"]
    )
    return 0 if required else 1


if __name__ == "__main__":
    raise SystemExit(main())

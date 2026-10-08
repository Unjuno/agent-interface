"""Offline Codex App Server ExternalMessage image-delivery regression.

This exercises the local App Server against a loopback-only mock Responses API.
It never contacts a model service or controls the game.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import queue
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any


SEQ = 200
EVENT_TEXT = "Fresh observation seq=200; HUD health 51, ammo 38."
IMAGE_SHA256 = "0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c"
MOCK_TEXT = "mock final"

def turn_id_from_reply(reply: dict[str, Any]) -> str | None:
    result = reply.get("result") if isinstance(reply, dict) else None
    turn = result.get("turn") if isinstance(result, dict) else None
    identifier = turn.get("id") if isinstance(turn, dict) else None
    return identifier if isinstance(identifier, str) and identifier else None


def inspect_requests(
    requests: list[dict[str, Any]], image: bytes, observation: str,
    initial_turn_id: str, external_turn_id: str | None,
) -> dict[str, Any]:
    all_input = json.dumps(requests, separators=(",", ":"))
    image_data = "data:image/png;base64," + base64.b64encode(image).decode("ascii")
    function_outputs = [
        item
        for request in requests
        for item in request.get("input", [])
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    ]
    output_json = json.dumps(function_outputs, separators=(",", ":"))
    return {
        "mock_request_count": len(requests),
        "same_turn_id": bool(initial_turn_id and external_turn_id and initial_turn_id == external_turn_id),
        "observation_text": observation,
        "text_delivered": observation in output_json,
        "image_delivered": image_data in output_json,
        "image_sha256": hashlib.sha256(image).hexdigest(),
        "image_bytes": len(image),
        "request_input_types": [
            [x.get("type") for x in r.get("input", []) if isinstance(x, dict)]
            for r in requests
        ],
        "observation_in_first_request": observation in json.dumps(requests[0]) if requests else False,
        "image_in_second_request": image_data in json.dumps(requests[1]) if len(requests) > 1 else False,
        "input_image_count": output_json.count('"type":"input_image"'),
        "request_ids": [r.get("model") for r in requests],
        "all_mock_input_sha256": hashlib.sha256(all_input.encode()).hexdigest(),
    }


def _response_sse(index: int) -> bytes:
    response_id = f"resp_{index}"
    message_id = f"msg_{index}"
    response = {
        "id": response_id, "object": "response", "created_at": 1,
        "status": "completed", "model": "gpt-5.6-luna",
        "output": [{
            "id": message_id, "type": "message", "status": "completed",
            "role": "assistant",
            "content": [{"type": "output_text", "text": MOCK_TEXT, "annotations": []}],
        }],
        "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
    }
    events = [
        ("response.created", {"response": {k: v for k, v in response.items() if k != "output"} | {"status": "in_progress", "output": []}}),
        ("response.output_item.added", {"output_index": 0, "item": {"id": message_id, "type": "message", "status": "in_progress", "role": "assistant", "content": []}}),
        ("response.content_part.added", {"item_id": message_id, "output_index": 0, "content_index": 0, "part": {"type": "output_text", "text": ""}}),
        ("response.output_text.delta", {"item_id": message_id, "output_index": 0, "content_index": 0, "delta": MOCK_TEXT}),
        ("response.output_text.done", {"item_id": message_id, "output_index": 0, "content_index": 0, "text": MOCK_TEXT}),
        ("response.content_part.done", {"item_id": message_id, "output_index": 0, "content_index": 0, "part": {"type": "output_text", "text": MOCK_TEXT}}),
        ("response.output_item.done", {"output_index": 0, "item": response["output"][0]}),
        ("response.completed", {"response": response}),
    ]
    chunks = []
    for event, fields in events:
        payload = {"type": event, **fields}
        chunks.append(f"event: {event}\ndata: {json.dumps(payload)}\n\n")
    return "".join(chunks).encode("utf-8")


class _MockState:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.first_request = threading.Event()
        self.release_first = threading.Event()
        self.errors: list[str] = []
        self.lock = threading.Lock()


def run_probe(image: bytes, detail: str, timeout: float = 20.0) -> dict[str, Any]:
    state = _MockState()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_: Any) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802
            try:
                size = int(self.headers.get("Content-Length", "0"))
                request = json.loads(self.rfile.read(size))
                with state.lock:
                    state.requests.append(request)
                    index = len(state.requests)
                if index == 1:
                    state.first_request.set()
                    if not state.release_first.wait(timeout):
                        state.errors.append("initial mock response release timed out")
                        self.send_error(504)
                        return
                body = _response_sse(index)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                self.wfile.flush()
            except Exception as exc:  # surfaced in the final assertions
                state.errors.append(f"mock handler: {type(exc).__name__}: {exc}")
                try:
                    self.send_error(500)
                except OSError:
                    pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    home = Path(tempfile.mkdtemp(prefix="codex-live-observation-a02-"))
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
''', encoding="utf-8",
    )
    env = os.environ.copy()
    env["CODEX_HOME"] = str(home)
    env.pop("OPENAI_API_KEY", None)
    process = subprocess.Popen(
        ["codex", "app-server", "--listen", "stdio://"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", bufsize=1, env=env, cwd=str(home),
    )
    messages: queue.Queue[dict[str, Any]] = queue.Queue()
    stderr: list[str] = []

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
        observed = []
        while time.monotonic() < end:
            try:
                message = messages.get(timeout=max(0.01, end - time.monotonic()))
            except queue.Empty:
                break
            observed.append(message)
            if predicate(message):
                return message
        raise TimeoutError(json.dumps(observed[-8:], default=str))

    try:
        send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "live-observation-a02", "title": "offline protocol regression", "version": "1"}}})
        init = wait_for(lambda m: m.get("id") == 1)
        send({"method": "initialized"})
        send({"id": 2, "method": "thread/start", "params": {"cwd": str(home), "model": "gpt-5.6-luna", "modelProvider": "mock", "approvalPolicy": "never", "sandbox": "read-only"}})
        thread_reply = wait_for(lambda m: m.get("id") == 2)
        if "error" in thread_reply:
            raise RuntimeError(json.dumps(thread_reply))
        thread_id = thread_reply["result"]["thread"]["id"]
        send({"id": 3, "method": "turn/start", "params": {"threadId": thread_id, "input": [{"type": "text", "text": "Say exactly INITIAL."}]}})
        initial_reply = wait_for(lambda m: m.get("id") == 3)
        if "error" in initial_reply:
            raise RuntimeError(json.dumps(initial_reply))
        turn_id = initial_reply["result"]["turn"]["id"]
        if not state.first_request.wait(12):
            raise TimeoutError("initial request did not reach loopback mock")
        tool_output = {
            "threadId": thread_id,
            "input": [],
            "toolOutput": {
                "name": "live_observation", "namespace": "agent-interface",
                "output": [
                    {"type": "input_text", "text": EVENT_TEXT},
                    {"type": "input_image", "image_url": "data:image/png;base64," + base64.b64encode(image).decode("ascii"), "detail": detail},
                ],
            },
        }
        send({"id": 4, "method": "turn/start", "params": tool_output})
        external_reply = wait_for(lambda m: m.get("id") == 4)
        state.release_first.set()
        deadline = time.monotonic() + timeout
        completed = None
        while time.monotonic() < deadline:
            try:
                message = messages.get(timeout=0.1)
            except queue.Empty:
                continue
            if message.get("method") == "turn/completed" and message.get("params", {}).get("turn", {}).get("id") == turn_id:
                completed = message
                break
        external_turn_id = turn_id_from_reply(external_reply)
        result = inspect_requests(state.requests, image, EVENT_TEXT, turn_id, external_turn_id)
        result.update({
            "cli_version": subprocess.check_output(["codex", "--version"], text=True).strip(),
            "loopback_only": True,
            "temporary_codex_home": True,
            "initialization_ok": "result" in init,
            "thread_started": "result" in thread_reply,
            "external_turn_start_response": external_reply,
            "external_turn_accepted": "result" in external_reply,
            "external_turn_id": external_turn_id,
            "turn_completed": completed is not None,
            "server_errors": state.errors,
            "app_server_stderr": "".join(stderr)[-2000:],
            "image_detail": detail,
        })
        return result
    finally:
        state.release_first.set()
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
    parser.add_argument("--frame", type=Path, required=True, help="retained PNG for event sequence 200")
    parser.add_argument("--detail", choices=("low", "auto"), default="auto")
    args = parser.parse_args()
    frame = args.frame.read_bytes()
    digest = hashlib.sha256(frame).hexdigest()
    if digest != IMAGE_SHA256:
        raise SystemExit(f"unexpected retained frame sha256: {digest}")
    result = run_probe(frame, args.detail)
    result["frame_sequence"] = SEQ
    result["frame_sha256_expected"] = IMAGE_SHA256
    print(json.dumps(result, indent=2))
    required = (
        result["initialization_ok"] and result["thread_started"]
        and result["external_turn_accepted"] and result["same_turn_id"] and result["turn_completed"]
        and result["text_delivered"]
        and result["image_delivered"] and result["image_in_second_request"]
        and not result["server_errors"] and len(result["request_input_types"]) >= 2
    )
    return 0 if required else 1


if __name__ == "__main__":
    raise SystemExit(main())

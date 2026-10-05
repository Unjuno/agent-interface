"""Measure how two active-turn observations appear in follow-up model requests.

The App Server uses a loopback-only mock Responses endpoint. No model service or
game process is contacted. The first HTTP model request is held behind an event
while two toolOutput observations are sent to the active turn.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any


EXPECTED_CLI_VERSION = "codex-cli 0.160.0"
EXPECTED_BASE_COMMIT = "2f2c83c3da36566bac410b13b2ed5202c9641f1a"
EXPECTED_CODEX_SHA256 = "37762753b554982eef1c109303d1be652b6397f1479e844794353a85650199c6"
OBSERVATIONS = (
    (201, "A04 observation seq=201; synthetic frame alpha."),
    (202, "A04 observation seq=202; synthetic frame beta."),
)
FRAME_SHA256S = (
    "b6ae54e7c1b64efe1de3170c9ec6cb70bbb4b4ca11de074ccaf7d21289382c70",
    "bb093ed0d73af55e49b3d971605a64ddd774ea335022305ef2454b58f3dd5220",
)
MOCK_TEXT = "mock final"
INITIAL_PENDING_WINDOW_S = 2.0
PROTOCOL_TIMEOUT_S = 20.0


def classify_deliveries(deliveries):
    """Classify paired text/image deliveries for observations 201 and 202."""
    if type(deliveries) is not list or len(deliveries) != 2:
        return "UNVERIFIABLE"
    paired = [row.get("paired") is True for row in deliveries]
    if paired == [True, True]:
        request_ids = [row.get("request_index") for row in deliveries]
        text_positions = [row.get("text_position") for row in deliveries]
        image_positions = [row.get("image_position") for row in deliveries]
        if any(type(value) is not int or value < 0
               for value in request_ids + text_positions + image_positions):
            return "UNVERIFIABLE"
        if request_ids[0] > request_ids[1]:
            return "BOTH_REVERSED"
        if request_ids[0] == request_ids[1]:
            if not (text_positions[0] < image_positions[0]
                    < text_positions[1] < image_positions[1]):
                return "BOTH_UNORDERED"
            return "BOTH_IN_ONE_FOLLOWUP_ORDERED"
        if any(text_positions[index] >= image_positions[index] for index in range(2)):
            return "BOTH_UNORDERED"
        return "BOTH_ACROSS_FOLLOWUPS_ORDERED"
    if paired == [False, True]:
        return "LATEST_ONLY"
    if paired == [True, False]:
        return "FIRST_ONLY"
    if any(row.get("text_seen") or row.get("image_seen") for row in deliveries):
        return "PARTIAL_OR_UNVERIFIABLE"
    return "NEITHER_OBSERVED"


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
        self.release_responses = threading.Event()
        self.first_response_release_ns: int | None = None
        self.first_response_sent_ns: int | None = None
        self.next_response_index = 1
        self.response_condition = threading.Condition()
        self.errors: list[str] = []
        self.lock = threading.Lock()


def inspect_requests(
    requests: list[dict[str, Any]], frames: list[bytes]
) -> dict[str, Any]:
    image_data = [
        "data:image/png;base64," + base64.b64encode(frame).decode("ascii")
        for frame in frames
    ]
    function_outputs = [
        item
        for request in requests
        for item in request.get("input", [])
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    ]
    deliveries = []
    per_request = []
    for request_index, request in enumerate(requests):
        serialized = json.dumps(request, separators=(",", ":"))
        per_request.append(serialized)
        for observation_index, (_, text) in enumerate(OBSERVATIONS):
            text_position = serialized.find(text)
            image_position = serialized.find(image_data[observation_index])
            paired_rows = [
                item for item in request.get("input", [])
                if isinstance(item, dict)
                and item.get("type") == "function_call_output"
                and text in json.dumps(item, separators=(",", ":"))
                and image_data[observation_index] in json.dumps(item, separators=(",", ":"))
            ]
            if text_position >= 0 or image_position >= 0:
                deliveries.append({
                    "observation_seq": OBSERVATIONS[observation_index][0],
                    "request_index": request_index,
                    "paired": bool(paired_rows),
                    "text_seen": text_position >= 0,
                    "image_seen": image_position >= 0,
                    "text_position": text_position if text_position >= 0 else None,
                    "image_position": image_position if image_position >= 0 else None,
                })
    ordered_deliveries = []
    for sequence, _ in OBSERVATIONS:
        matches = [row for row in deliveries if row["observation_seq"] == sequence]
        if len(matches) == 1:
            ordered_deliveries.append(matches[0])
        elif not matches:
            ordered_deliveries.append({
                "observation_seq": sequence, "request_index": -1,
                "paired": False, "text_seen": False, "image_seen": False,
                "text_position": -1, "image_position": -1,
            })
        else:
            ordered_deliveries.append({
                "observation_seq": sequence, "request_index": -1,
                "paired": False,
                "text_seen": any(row["text_seen"] for row in matches),
                "image_seen": any(row["image_seen"] for row in matches),
                "text_position": -1, "image_position": -1,
            })
    return {
        "mock_request_count": len(requests),
        "observations": [
            {"sequence": sequence, "text": text,
             "frame_sha256": hashlib.sha256(frames[index]).hexdigest(),
             "frame_bytes": len(frames[index])}
            for index, (sequence, text) in enumerate(OBSERVATIONS)
        ],
        "deliveries": ordered_deliveries,
        "delivery_class": classify_deliveries(ordered_deliveries),
        "all_observations_in_followups": all(
            row["paired"] and row["request_index"] > 0 for row in ordered_deliveries
        ),
        "followup_request_input_types": [
            [row.get("type") for row in request.get("input", []) if isinstance(row, dict)]
            for request in requests[1:]
        ],
        "raw_requests": requests,
    }


def _run_app_server(frames: list[bytes], pending_window_s: float) -> dict[str, Any]:
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
                if not state.release_responses.wait(PROTOCOL_TIMEOUT_S):
                    state.errors.append(f"mock response gate timed out for request {index}")
                    self.send_error(504)
                    return
                with state.response_condition:
                    deadline = time.monotonic() + PROTOCOL_TIMEOUT_S
                    while state.next_response_index != index:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            state.errors.append(f"response ordering timed out for request {index}")
                            self.send_error(504)
                            return
                        state.response_condition.wait(remaining)

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
                with state.response_condition:
                    state.next_response_index += 1
                    state.response_condition.notify_all()
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
    protocol_messages: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="codex-live-observation-a04-") as home_text:
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
        removed_environment = []
        for key in (
            "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID",
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy",
        ):
            if key in env:
                removed_environment.append(key)
            env.pop(key, None)
        codex_executable = shutil.which("codex")
        if codex_executable is None:
            raise RuntimeError("codex executable was not found on PATH")
        codex_sha256 = hashlib.sha256(Path(codex_executable).read_bytes()).hexdigest()
        if codex_sha256 != EXPECTED_CODEX_SHA256:
            raise RuntimeError(f"unexpected codex executable SHA-256: {codex_sha256}")
        process = subprocess.Popen(
            [codex_executable, "app-server", "--listen", "stdio://"],
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
                    message = json.loads(line)
                except json.JSONDecodeError:
                    message = {"_raw": line}
                protocol_messages.append(message)
                messages.put(message)

        def read_stderr() -> None:
            assert process.stderr
            stderr.extend(process.stderr.readlines())

        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()

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
        external_replies: list[dict[str, Any]] = []
        initial_turn_id: str | None = None
        completed: dict[str, Any] | None = None
        try:
            codex_version = subprocess.check_output([codex_executable, "--version"], text=True).strip()
            if codex_version != EXPECTED_CLI_VERSION:
                raise RuntimeError(f"expected {EXPECTED_CLI_VERSION}, got {codex_version}")

            send({"id": 1, "method": "initialize", "params": {
                "clientInfo": {"name": "v39-observation-a04", "title": "offline observation queue composition", "version": "1"}
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

            observation_ack_ns: list[int] = []
            for rpc_id, ((sequence, observation_text), frame) in enumerate(
                zip(OBSERVATIONS, frames, strict=True), start=4
            ):
                observation = {
                    "threadId": thread_id,
                    "input": [],
                    "toolOutput": {
                        "name": "live_observation",
                        "namespace": "agent-interface",
                        "output": [
                            {"type": "input_text", "text": observation_text},
                            {"type": "input_image", "image_url":
                             "data:image/png;base64," + base64.b64encode(frame).decode("ascii"),
                             "detail": "auto"},
                        ],
                    },
                }
                send({"id": rpc_id, "method": "turn/start", "params": observation})
                reply = wait_for(lambda message, expected_id=rpc_id: message.get("id") == expected_id)
                observation_ack_ns.append(time.monotonic_ns())
                external_replies.append(reply)

            # Keep every mock Responses request unresolved until both observations
            # have been acknowledged and the fixed pending window has elapsed.
            time.sleep(pending_window_s)
            with state.lock:
                followup_request_count_before_release = max(0, len(state.requests) - 1)
            state.first_response_release_ns = time.monotonic_ns()
            state.release_responses.set()

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

            with state.lock:
                requests = list(state.requests)
            inspected = inspect_requests(requests, frames)
            inspected.update({
                "cli_version": codex_version,
                "codex_executable": codex_executable,
                "codex_executable_sha256": codex_sha256,
                "base_commit": EXPECTED_BASE_COMMIT,
                "loopback_only": True,
                "temporary_codex_home": True,
                "network_override_keys_removed": removed_environment,
                "initialize_ok": "result" in initialize_reply,
                "thread_started": "result" in thread_reply,
                "observation_rpc_accepted_count": sum("result" in reply for reply in external_replies),
                "observation_rpc_replies": external_replies,
                "app_server_protocol_messages": protocol_messages,
                "initial_turn_id": initial_turn_id,
                "external_turn_ids": [turn_id_from_start_reply(reply) for reply in external_replies],
                "external_turn_statuses_at_ack": [
                    reply.get("result", {}).get("turn", {}).get("status")
                    for reply in external_replies
                ],
                "same_turn_ids": all(
                    turn_id_from_start_reply(reply) == initial_turn_id
                    for reply in external_replies
                ),
                "observation_ack_ns": observation_ack_ns,
                "followup_request_count_before_release": followup_request_count_before_release,
                "request_received_ns": list(state.request_received_ns),
                "first_response_release_ns": state.first_response_release_ns,
                "first_response_sent_ns": state.first_response_sent_ns,
                "turn_completed": completed is not None,
                "server_errors": list(state.errors),
                "app_server_stderr": "".join(stderr),
            })
            if inspected["observation_rpc_accepted_count"] != len(OBSERVATIONS):
                inspected["delivery_class"] = "RPC_REJECTED"
            elif not inspected["same_turn_ids"] or inspected["external_turn_statuses_at_ack"] != [
                "inProgress"
            ] * len(OBSERVATIONS):
                inspected["delivery_class"] = "UNVERIFIABLE"
            return inspected
        finally:
            state.release_responses.set()
            if process.stdin:
                process.stdin.close()
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            stdout_thread.join(timeout=3)
            stderr_thread.join(timeout=3)
            if "inspected" in locals():
                inspected["app_server_stderr"] = "".join(stderr)
                inspected["app_server_stdout_capture_complete"] = not stdout_thread.is_alive()
                inspected["app_server_stderr_capture_complete"] = not stderr_thread.is_alive()
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame-201", type=Path, required=True)
    parser.add_argument("--frame-202", type=Path, required=True)
    args = parser.parse_args()
    frames = [args.frame_201.read_bytes(), args.frame_202.read_bytes()]
    frame_hashes = [hashlib.sha256(frame).hexdigest() for frame in frames]
    if frame_hashes != list(FRAME_SHA256S):
        raise SystemExit(f"unexpected frozen PNG hashes: {frame_hashes}")
    result = _run_app_server(frames, INITIAL_PENDING_WINDOW_S)
    result["frame_sha256_expected"] = list(FRAME_SHA256S)
    result["frame_sequences"] = [sequence for sequence, _ in OBSERVATIONS]
    print(json.dumps(result, indent=2, sort_keys=True))
    required = (
        result["initialize_ok"] and result["thread_started"]
        and len(result.get("observation_rpc_replies", [])) == len(OBSERVATIONS)
        and result["turn_completed"] and result["mock_request_count"] >= 1
        and result["first_response_sent_ns"] is not None
        and not result["server_errors"]
        and result["delivery_class"] not in {
            "UNVERIFIABLE", "PARTIAL_OR_UNVERIFIABLE"
        }
    )
    return 0 if required else 1


if __name__ == "__main__":
    raise SystemExit(main())

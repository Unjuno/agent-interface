"""One-shot local app-server -> mock Responses -> dynamic-tool round trip."""
from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import pathlib
import queue
import socket
import subprocess
import tempfile
import threading
import time
import urllib.parse


ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / "RAW.json"
IMAGE = ROOT / "input-g18-final.png"
APP_SERVER = pathlib.Path(
    "/Applications/ChatGPT.app/Contents/Resources/codex-cli/"
    "CodexCLI.app/Contents/MacOS/codex"
)
EXPECTED_IMAGE_SHA256 = "6331fd4bb0f62dbb6d8492e0c71a4ad6bf1b98091f39b452e2279e7cfd3e6bcf"
PARTIAL_TEXT = (
    "PARTIAL_STATE=SAFE_YIELD; reason=effect_unavailable; "
    "completed_transitions=1; second_requested_input=NOT_RUN; "
    "saved_cells=13,41,533; next_row=BLANK"
)
TOOL_NAME = "emit_partial"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def summarize(value):
    texts: list[str] = []
    images: list[str] = []
    types: list[str] = []

    def walk(item):
        if isinstance(item, dict):
            t = item.get("type")
            if isinstance(t, str):
                types.append(t)
            for key, child in item.items():
                if isinstance(child, str):
                    if key in {"text", "output", "arguments"} and len(child) < 100_000:
                        texts.append(child)
                    if child.startswith("data:image/png;base64,"):
                        try:
                            images.append(sha256(base64.b64decode(child.split(",", 1)[1], validate=True)))
                        except Exception:
                            images.append("INVALID_DATA_URI")
                else:
                    walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    public_texts = []
    redacted_texts = []
    safe_exact = {
        PARTIAL_TEXT,
        "Run the registered protocol probe tool exactly once.",
        "{}",
        "MOCK_FINAL: partial evidence was delivered; no task completion is asserted.",
    }
    for text in texts:
        safe = PARTIAL_TEXT if PARTIAL_TEXT in text else text
        if safe in safe_exact:
            public_texts.append(safe)
        else:
            redacted_texts.append({"sha256": sha256(text.encode("utf-8")), "bytes": len(text.encode("utf-8"))})
    return {
        "body_sha256": sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()),
        "model": value.get("model") if isinstance(value, dict) else None,
        "stream": value.get("stream") if isinstance(value, dict) else None,
        "input_item_types": types,
        "text_fragments": public_texts,
        "redacted_text_fragment_count": len(redacted_texts),
        "redacted_text_fragments": redacted_texts,
        "data_image_sha256s": images,
        "top_level_keys": sorted(value) if isinstance(value, dict) else [],
    }


def response_events(turn: int) -> list[dict]:
    if turn == 1:
        call = {
            "id": "fc_local_1",
            "type": "function_call",
            "status": "completed",
            "call_id": "call_local_1",
            "name": TOOL_NAME,
            "arguments": "{}",
        }
        final_item = call
        events = [
            {"type": "response.created", "response": {"id": "resp_local_1", "object": "response", "status": "in_progress", "output": []}},
            {"type": "response.output_item.added", "response_id": "resp_local_1", "output_index": 0, "item": {**call, "status": "in_progress", "arguments": ""}},
            {"type": "response.function_call_arguments.delta", "item_id": "fc_local_1", "output_index": 0, "delta": "{}"},
            {"type": "response.function_call_arguments.done", "item_id": "fc_local_1", "output_index": 0, "arguments": "{}"},
            {"type": "response.output_item.done", "response_id": "resp_local_1", "output_index": 0, "item": call},
        ]
        completed = {"id": "resp_local_1", "object": "response", "status": "completed", "output": [final_item], "usage": {"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}}
    else:
        message = {
            "id": "msg_local_2",
            "type": "message",
            "status": "completed",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "MOCK_FINAL: partial evidence was delivered; no task completion is asserted."}],
        }
        events = [
            {"type": "response.created", "response": {"id": "resp_local_2", "object": "response", "status": "in_progress", "output": []}},
            {"type": "response.output_item.added", "response_id": "resp_local_2", "output_index": 0, "item": {**message, "status": "in_progress", "content": []}},
            {"type": "response.content_part.added", "item_id": "msg_local_2", "output_index": 0, "content_index": 0, "part": {"type": "output_text", "text": ""}},
            {"type": "response.output_text.delta", "item_id": "msg_local_2", "output_index": 0, "content_index": 0, "delta": "MOCK_FINAL: partial evidence was delivered; no task completion is asserted."},
            {"type": "response.output_text.done", "item_id": "msg_local_2", "output_index": 0, "content_index": 0, "text": "MOCK_FINAL: partial evidence was delivered; no task completion is asserted."},
            {"type": "response.content_part.done", "item_id": "msg_local_2", "output_index": 0, "content_index": 0, "part": {"type": "output_text", "text": "MOCK_FINAL: partial evidence was delivered; no task completion is asserted."}},
            {"type": "response.output_item.done", "response_id": "resp_local_2", "output_index": 0, "item": message},
        ]
        completed = {"id": "resp_local_2", "object": "response", "status": "completed", "output": [message], "usage": {"input_tokens": 9, "output_tokens": 12, "total_tokens": 21}}
    events.append({"type": "response.completed", "response": completed})
    return events


class MockState:
    def __init__(self):
        self.requests: list[dict] = []
        self.lock = threading.Lock()


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        return

    def do_POST(self):
        state: MockState = self.server.state  # type: ignore[attr-defined]
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw)
        except Exception:
            self.send_error(400)
            return
        if urllib.parse.urlsplit(self.path).path != "/v1/responses":
            self.send_error(404)
            return
        with state.lock:
            state.requests.append(summarize(body))
            turn = len(state.requests)
        if turn > 2:
            self.send_error(409, "unexpected extra model request")
            return
        payload = b"".join(
            (b"event: " + event["type"].encode() + b"\ndata: " + json.dumps(event, separators=(",", ":")).encode() + b"\n\n")
            for event in response_events(turn)
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)
        self.wfile.flush()
        self.close_connection = True


def run_experiment() -> int:
    if RAW.exists():
        raise SystemExit("refusing to overwrite existing RAW.json")
    if not APP_SERVER.is_file():
        raise SystemExit("ChatGPT-bundled app-server binary unavailable")
    image_bytes = IMAGE.read_bytes()
    image_digest = sha256(image_bytes)
    if image_digest != EXPECTED_IMAGE_SHA256:
        raise SystemExit("G18 input image digest mismatch")

    state = MockState()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.state = state  # type: ignore[attr-defined]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    app_version = subprocess.run([str(APP_SERVER), "--version"], check=True, capture_output=True, text=True).stdout.strip()
    app_binary_sha256 = sha256(APP_SERVER.read_bytes())
    rpc_queue: queue.Queue[dict] = queue.Queue()
    rpc_sent: list[str] = []
    rpc_methods: list[str] = []
    tool_results: list[dict] = []
    rpc_errors: list[dict] = []
    started = time.time_ns()
    with tempfile.TemporaryDirectory(prefix="codex-appserver-roundtrip-") as workdir:
        env = os.environ.copy()
        env["CODEX_LOCAL_MOCK_KEY"] = "local-only-test-key"
        env["NO_PROXY"] = "127.0.0.1,localhost"
        env["no_proxy"] = "127.0.0.1,localhost"
        command = [
            str(APP_SERVER), "app-server", "--stdio",
            "--disable", "plugins", "--disable", "apps", "--disable", "multi_agent",
            "--disable", "hooks", "--disable", "shell_tool", "--disable", "computer_use",
            "--disable", "browser_use", "--disable", "browser_use_external", "--disable", "unified_exec",
            "-c", "analytics.enabled=false",
            "-c", 'model_provider="local_mock"',
            "-c", 'model_providers.local_mock.name="Local mock"',
            "-c", f'model_providers.local_mock.base_url="http://127.0.0.1:{port}/v1"',
            "-c", 'model_providers.local_mock.env_key="CODEX_LOCAL_MOCK_KEY"',
            "-c", 'model_providers.local_mock.wire_api="responses"',
            "-c", 'model_providers.local_mock.requires_openai_auth=false',
            "-c", 'model_providers.local_mock.supports_websockets=false',
        ]
        app = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workdir, env=env, text=True, bufsize=1)

        def read_stdout():
            assert app.stdout is not None
            for line in app.stdout:
                try:
                    rpc_queue.put(json.loads(line))
                except Exception:
                    rpc_errors.append({"kind": "non_json_stdout", "line_sha256": sha256(line.encode())})

        reader = threading.Thread(target=read_stdout, daemon=True)
        reader.start()

        def send(obj):
            assert app.stdin is not None
            rpc_sent.append(obj.get("method", "response"))
            app.stdin.write(json.dumps(obj, separators=(",", ":")) + "\n")
            app.stdin.flush()

        def take_response(identity, deadline=25):
            end = time.monotonic() + deadline
            while time.monotonic() < end:
                try:
                    obj = rpc_queue.get(timeout=0.2)
                except queue.Empty:
                    if app.poll() is not None:
                        raise RuntimeError("app-server exited before JSON-RPC response")
                    continue
                method = obj.get("method")
                if method:
                    rpc_methods.append(method)
                if obj.get("id") == identity:
                    if "error" in obj:
                        raise RuntimeError("JSON-RPC error: " + json.dumps(obj["error"], sort_keys=True))
                    return obj.get("result")
                if obj.get("method") == "item/tool/call":
                    params = obj.get("params", {})
                    if params.get("tool") != TOOL_NAME:
                        raise RuntimeError("unexpected dynamic tool name")
                    tool_results.append(params)
                    call_id = obj["id"]
                    image_uri = "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")
                    send({"id": call_id, "result": {"success": True, "contentItems": [
                        {"type": "inputText", "text": PARTIAL_TEXT},
                        {"type": "inputImage", "imageUrl": image_uri},
                    ]}})
                elif obj.get("id") is not None and obj.get("method"):
                    raise RuntimeError("unexpected app-server request: " + str(obj.get("method")))
            raise TimeoutError("JSON-RPC response deadline")

        try:
            send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "agent-interface-context-probe", "title": "Agent Interface Context Probe", "version": "1"}, "capabilities": {"experimentalApi": True}}})
            initialized = take_response(1)
            send({"method": "initialized", "params": {}})
            params = {
                "model": "gpt-6.1-sol",
                "cwd": workdir,
                "ephemeral": True,
                "sandbox": "read-only",
                "approvalPolicy": "never",
                "environments": [],
                "selectedCapabilityRoots": [],
                "allowProviderModelFallback": False,
                "dynamicTools": [{"type": "function", "name": TOOL_NAME, "description": "Return one frozen partial-result payload to inspect app-server normalization.", "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}, "required": []}}],
                "baseInstructions": "This is a protocol probe. Call emit_partial exactly once and then report the literal payload marker returned by it. Do not claim task completion.",
                "config": {"project_doc_max_bytes": 0, "model_reasoning_effort": "low"},
            }
            send({"id": 2, "method": "thread/start", "params": params})
            thread_start = take_response(2)
            thread = thread_start["thread"]["id"]
            if thread_start.get("model") != "gpt-6.1-sol" or thread_start.get("reasoningEffort") != "low":
                raise RuntimeError("thread/start did not echo requested model/effort")
            send({"id": 3, "method": "turn/start", "params": {"threadId": thread, "effort": "low", "input": [{"type": "text", "text": "Run the registered protocol probe tool exactly once."}]}})
            turn_start = take_response(3)
            ended = time.monotonic() + 40
            completed = None
            while time.monotonic() < ended:
                try:
                    obj = rpc_queue.get(timeout=0.2)
                except queue.Empty:
                    if app.poll() is not None:
                        raise RuntimeError("app-server exited during turn")
                    continue
                method = obj.get("method")
                if method:
                    rpc_methods.append(method)
                if method == "item/tool/call":
                    params = obj.get("params", {})
                    if params.get("tool") != TOOL_NAME:
                        raise RuntimeError("unexpected dynamic tool name")
                    tool_results.append(params)
                    call_id = obj["id"]
                    image_uri = "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")
                    send({"id": call_id, "result": {"success": True, "contentItems": [
                        {"type": "inputText", "text": PARTIAL_TEXT},
                        {"type": "inputImage", "imageUrl": image_uri},
                    ]}})
                elif method == "turn/completed":
                    completed = obj.get("params", {}).get("turn", {})
                    break
                elif obj.get("id") is not None and method:
                    raise RuntimeError("unexpected app-server request during turn: " + str(method))
            if completed is None:
                raise TimeoutError("turn/completed deadline")
            if completed.get("status") != "completed":
                raise RuntimeError("turn did not complete")
            if len(tool_results) != 1:
                raise RuntimeError("expected exactly one dynamic-tool request")
            if len(state.requests) != 2:
                raise RuntimeError(f"expected two local Responses requests, got {len(state.requests)}")
            app.stdin.close()
            app.stdin = None
            try:
                exit_code = app.wait(timeout=10)
            except subprocess.TimeoutExpired:
                app.terminate()
                exit_code = app.wait(timeout=5)
            stderr = app.stderr.read() if app.stderr else b""
            if exit_code != 0:
                raise RuntimeError(f"app-server exit code {exit_code}; stderr sha256={sha256(stderr)}")
        except Exception:
            if app.poll() is None:
                app.terminate()
                app.wait(timeout=5)
            raise

    server.shutdown()
    server.server_close()
    server_thread.join(timeout=2)
    raw = {
        "disposition": "OBSERVED_LOCAL_APP_SERVER_CONTEXT_ROUNDTRIP",
        "scope": "one local app-server turn; mock Responses endpoint; no external provider, GUI, native input, or task-effect inference",
        "app_server_version": app_version,
        "app_server_binary_sha256": app_binary_sha256,
        "base_commit": "b84fc9a4fc14608c729e7eda2ee32ba6b4ac0ab4",
        "source_image_sha256": image_digest,
        "partial_text": PARTIAL_TEXT,
        "rpc_sent_methods": rpc_sent,
        "rpc_received_methods": rpc_methods,
        "dynamic_tool_calls": len(tool_results),
        "tool_result_success": True,
        "initialize_result_keys": sorted(initialized) if isinstance(initialized, dict) else [],
        "thread_started": bool(thread_start),
        "turn_started": bool(turn_start),
        "turn_status": completed.get("status"),
        "mock_responses_requests": state.requests,
        "started_wall_ns": started,
        "ended_wall_ns": time.time_ns(),
        "rpc_errors": rpc_errors,
    }
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": raw["disposition"], "app_server_version": app_version, "rounds": len(state.requests), "tool_calls": len(tool_results), "second_request_text": state.requests[-1]["text_fragments"], "second_request_image_sha256s": state.requests[-1]["data_image_sha256s"]}, sort_keys=True))
    return 0


def main() -> int:
    try:
        return run_experiment()
    except Exception as exc:
        raw_path = ROOT / "RAW.json"
        if not raw_path.exists():
            raw_path.write_text(json.dumps({
                "disposition": "STOP_LOCAL_APP_SERVER_CONTEXT_ROUNDTRIP",
                "exception_type": type(exc).__name__,
                "exception": str(exc)[:1000],
                "scope": "one local app-server turn; mock Responses endpoint; no external provider, GUI, native input, or task-effect inference",
            }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"disposition": "STOP_LOCAL_APP_SERVER_CONTEXT_ROUNDTRIP", "exception_type": type(exc).__name__, "exception": str(exc)[:300]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

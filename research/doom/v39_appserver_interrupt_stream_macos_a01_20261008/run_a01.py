import hashlib
import json
from datetime import datetime, timezone
import os
import select
import socket
import struct
import subprocess
import tempfile
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CLI = "/opt/homebrew/bin/codex"
EXPECTED_VERSION = "codex-cli 0.146.1"
PRE_RELEASE_WAIT_S = 2.0


def chunk(kind, payload):
    return (struct.pack("!I", len(payload)) + kind + payload +
            struct.pack("!I", zlib.crc32(kind + payload) & 0xffffffff))


def png_rgb_2x2():
    raw = b"\x00" + bytes((10, 20, 30)) * 2 + b"\x00" + bytes((40, 50, 60)) * 2
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack("!2I5B", 2, 2, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def sse(*events):
    return "".join("event: " + item["type"] + "\ndata: " +
                   json.dumps(item, separators=(",", ":")) + "\n\n"
                   for item in events).encode()


def mock_response(response_id):
    return sse(
        {"type": "response.created", "response": {"id": response_id}},
        {"type": "response.output_item.done", "item": {
            "type": "message", "role": "assistant", "id": "msg-" + response_id,
            "content": [{"type": "output_text", "text": '{"kind":"mock"}'}]}},
        {"type": "response.completed", "response": {
            "id": response_id, "usage": {"input_tokens": 3, "output_tokens": 2,
            "total_tokens": 5}}})


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)

    request_seen = threading.Event()
    stream_open = threading.Event()
    release_first = threading.Event()
    client_closed = threading.Event()
    state = {"requests": [], "events": [], "errors": [], "close_kind": None}
    lock = threading.Lock()

    def event(name, **fields):
        row = {"event": name, "monotonic_ns": time.monotonic_ns(), **fields}
        with lock:
            state["events"].append(row)
        return row

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
            try:
                raw = self.rfile.read(int(self.headers.get("content-length", "0")))
                try:
                    body = json.loads(raw)
                except Exception:
                    body = {}
                row = {
                    "path": self.path,
                    "peer_ip": self.client_address[0],
                    "peer_port": self.client_address[1],
                    "received_monotonic_ns": time.monotonic_ns(),
                    "body_sha256": hashlib.sha256(raw).hexdigest(),
                    "model": body.get("model"),
                }
                with lock:
                    state["requests"].append(row)
                request_seen.set()
                event("responses_request_received", index=len(state["requests"]) - 1)
                if not self.path.endswith("/responses"):
                    self.send_error(404)
                    return

                self.send_response(200)
                self.send_header("content-type", "text/event-stream")
                self.send_header("connection", "close")
                self.end_headers()
                self.wfile.write(sse({"type": "response.created",
                                      "response": {"id": "a01-response-1"}}))
                self.wfile.flush()
                stream_open.set()
                event("mock_response_created_sent")

                deadline = time.monotonic() + 8.0
                while not release_first.is_set() and time.monotonic() < deadline:
                    readable, _, _ = select.select([self.connection], [], [], 0.025)
                    if not readable:
                        continue
                    try:
                        peek = self.connection.recv(1, socket.MSG_PEEK)
                    except (ConnectionResetError, BrokenPipeError):
                        with lock:
                            state["close_kind"] = "reset"
                        event("provider_socket_reset_before_release")
                        client_closed.set()
                        return
                    except OSError as error:
                        with lock:
                            state["errors"].append(type(error).__name__)
                        return
                    if peek == b"":
                        with lock:
                            state["close_kind"] = "eof"
                        event("provider_socket_eof_before_release")
                        client_closed.set()
                        return
                    # Unexpected client payload is not consumed; keep the bounded observation.
                    event("unexpected_client_payload_while_waiting", byte_count=len(peek))
                    time.sleep(0.025)

                if not release_first.is_set():
                    with lock:
                        state["errors"].append("mock_hold_timeout")
                    return
                event("mock_response_release_observed")
                payload = mock_response("a01-response-1")
                self.wfile.write(payload)
                self.wfile.flush()
                event("mock_response_written")
            except (BrokenPipeError, ConnectionResetError):
                with lock:
                    state["errors"].append("write_after_close")
            except Exception as error:
                with lock:
                    state["errors"].append(type(error).__name__)
            finally:
                self.close_connection = True

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    process = None
    result = {"disposition": "HOLD_SETUP_OR_TRANSPORT", "app_server_version": None,
              "run_started_at_utc": datetime.now(timezone.utc).isoformat()}
    stderr_bytes = bytearray()
    stage = "cli_version_preflight"
    try:
        version = subprocess.run([CLI, "--version"], capture_output=True,
                                 text=True, timeout=3).stdout.strip()
        result["app_server_version"] = version
        if version != EXPECTED_VERSION:
            result["disposition"] = "STOP_UNEXPECTED_APP_SERVER_VERSION"
            raise RuntimeError("installed App Server version differs from frozen expectation")

        stage = "isolated_home_setup"
        scratch = Path(tempfile.mkdtemp(prefix="codex-stream-cancel-a01-"))
        home, cwd, tmp = scratch / "home", scratch / "cwd", scratch / "tmp"
        home.mkdir()
        cwd.mkdir()
        tmp.mkdir()
        (home / "config.toml").write_text(
            'model = "mock-model"\nmodel_provider = "mock_provider"\n'
            'approval_policy = "never"\nsandbox_mode = "read-only"\n'
            '[model_providers.mock_provider]\nname = "local mock"\n'
            f'base_url = "http://127.0.0.1:{server.server_port}/v1"\n'
            'wire_api = "responses"\nrequires_openai_auth = false\n'
            'supports_websockets = false\nrequest_max_retries = 0\n'
            'stream_max_retries = 0\n[analytics]\nenabled = false\n',
            encoding="utf-8")
        env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
               "HOME": str(home), "CODEX_HOME": str(home), "TMPDIR": str(tmp),
               "CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG": "1",
               "RUST_LOG": "warn", "LANG": "en_US.UTF-8"}
        result["credentials_passed_to_app_server"] = any(
            key in env for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"))
        stage = "app_server_startup"
        process = subprocess.Popen([CLI, "app-server", "--stdio"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1, env=env, cwd=str(cwd))
        rows, rows_lock = [], threading.Lock()

        def read_stdout():
            for line in process.stdout:
                try:
                    parsed = json.loads(line)
                except Exception:
                    continue
                with rows_lock:
                    rows.append((time.monotonic_ns(), parsed))

        def read_stderr():
            for line in process.stderr:
                stderr_bytes.extend(line.encode("utf-8", errors="replace"))

        threading.Thread(target=read_stdout, daemon=True).start()
        threading.Thread(target=read_stderr, daemon=True).start()
        write_lock = threading.Lock()
        next_id = 0

        def send(method, params):
            nonlocal next_id
            next_id += 1
            request_id = next_id
            with write_lock:
                process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id,
                    "method": method, "params": params}) + "\n")
                process.stdin.flush()
            return request_id

        def wait_response(request_id, timeout=6.0):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                with rows_lock:
                    for _, row in rows:
                        if row.get("id") == request_id:
                            return row
                if process.poll() is not None:
                    break
                time.sleep(0.01)
            raise TimeoutError("missing JSON-RPC response")

        def completion(thread_id, turn_id):
            with rows_lock:
                for observed_ns, row in rows:
                    if (row.get("method") == "turn/completed" and
                        row.get("params", {}).get("threadId") == thread_id and
                        row.get("params", {}).get("turn", {}).get("id") == turn_id):
                        return observed_ns, row["params"]["turn"]
            return None

        def wait_event(waitable, timeout):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if waitable.is_set():
                    return True
                if process.poll() is not None:
                    return False
                time.sleep(0.01)
            return waitable.is_set()

        stage = "initialize"
        wait_response(send("initialize", {"clientInfo": {"name": "cancel-a01",
            "title": "stream cancellation portability", "version": "1"},
            "capabilities": {"experimentalApi": False, "requestAttestation": False}}))
        with write_lock:
            process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "initialized",
                                            "params": {}}) + "\n")
            process.stdin.flush()
        stage = "thread_start"
        thread_row = wait_response(send("thread/start", {"model": "mock-model",
            "cwd": str(cwd), "approvalPolicy": "never", "sandbox": "read-only",
            "baseInstructions": "Use only the supplied test request.",
            "ephemeral": True, "threadSource": "exec"}))
        thread_id = thread_row.get("result", {}).get("thread", {}).get("id")
        if not thread_id:
            raise RuntimeError("thread/start returned no thread id")
        stage = "initial_turn_start"
        turn_row = wait_response(send("turn/start", {"threadId": thread_id,
            "input": [{"type": "text", "text": "Initial pending request",
                       "text_elements": []}], "model": "mock-model", "effort": "low",
            "outputSchema": {"type": "object", "properties": {
                "kind": {"type": "string"}}, "required": ["kind"],
                "additionalProperties": False}}))
        turn_id = turn_row.get("result", {}).get("turn", {}).get("id")
        if not turn_id:
            raise RuntimeError("turn/start returned no turn id")
        if not wait_event(stream_open, 6.0):
            raise TimeoutError("mock did not open a pending Responses stream")

        stage = "pending_response_interrupt"
        result["pending_request_observed"] = True
        result["interrupt_sent_at_ns"] = time.monotonic_ns()
        interrupt_row = wait_response(send("turn/interrupt", {
            "threadId": thread_id, "turnId": turn_id}), timeout=4.0)
        result["interrupt_ack_at_ns"] = time.monotonic_ns()
        result["interrupt_rpc_accepted"] = "error" not in interrupt_row
        result["interrupt_rpc_error"] = "error" in interrupt_row
        event("interrupt_rpc_acknowledged", accepted=result["interrupt_rpc_accepted"])
        if result["interrupt_rpc_accepted"]:
            wait_event(client_closed, PRE_RELEASE_WAIT_S)
        close_event = next((row for row in list(state["events"])
                            if row["event"] in ("provider_socket_eof_before_release",
                                                "provider_socket_reset_before_release")), None)
        result["pre_release_wait_seconds"] = PRE_RELEASE_WAIT_S
        result["response_release_at_ns"] = time.monotonic_ns()
        result["provider_socket_close_kind_before_release"] = state["close_kind"]
        result["provider_socket_closed_before_release"] = close_event is not None and (
            close_event["monotonic_ns"] < result["response_release_at_ns"])
        result["provider_socket_close_at_ns"] = close_event["monotonic_ns"] if close_event else None
        event("response_release_gate_set")
        release_first.set()

        deadline = time.monotonic() + 5.0
        observed = None
        while time.monotonic() < deadline:
            observed = completion(thread_id, turn_id)
            if observed:
                break
            if process.poll() is not None:
                break
            time.sleep(0.01)
        result["matching_turn_completion_observed"] = observed is not None
        result["turn_completion_status"] = observed[1].get("status") if observed else None
        result["turn_completion_at_ns"] = observed[0] if observed else None
        result["completion_thread_matches"] = bool(observed and thread_id)
        result["completion_turn_matches"] = bool(observed and turn_id)
        with lock:
            result["mock_request_count"] = len(state["requests"])
            result["mock_requests"] = list(state["requests"])
            result["mock_events"] = list(state["events"])
            result["mock_errors"] = list(state["errors"])
        result["mock_listener_ip"] = server.server_address[0]
        result["mock_listener_port"] = server.server_port
        result["app_server_stderr_nonempty"] = bool(stderr_bytes)
        result["app_server_stderr_sha256"] = hashlib.sha256(stderr_bytes).hexdigest()
        result["disposition"] = (
            "PASS_INTERRUPT_CLOSED_PENDING_PROVIDER_STREAM_BEFORE_RELEASE"
            if result["interrupt_rpc_accepted"] and
            result["provider_socket_closed_before_release"] and
            result["matching_turn_completion_observed"] and
            result["turn_completion_status"] == "interrupted" and
            result["mock_request_count"] == 1 and not result["mock_errors"]
            else "FAIL_STREAM_NOT_CLOSED_BEFORE_RELEASE"
            if result["interrupt_rpc_accepted"] and result["matching_turn_completion_observed"]
            else "HOLD_INCOMPLETE_TERMINAL_OR_TRANSPORT_EVIDENCE")
    except Exception as error:
        error_text = str(error)
        (out / "private_error.txt").write_text(error_text + "\n", encoding="utf-8")
        result.update({"disposition": result.get("disposition")
                       if str(result.get("disposition", "")).startswith("STOP_")
                       else "HOLD_HARNESS_OR_ISOLATION_ERROR",
                       "error_type": type(error).__name__, "error_phase": stage,
                       "error_message_sha256": hashlib.sha256(error_text.encode()).hexdigest()})
        with lock:
            result["mock_request_count"] = len(state["requests"])
            result["mock_requests"] = list(state["requests"])
            result["mock_events"] = list(state["events"])
            result["mock_errors"] = list(state["errors"])
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
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            result["app_server_exit_code"] = process.returncode
            if stderr_bytes:
                (out / "private_app_server_stderr.txt").write_bytes(bytes(stderr_bytes))
        else:
            result["app_server_exit_code"] = None
        result["run_finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                         encoding="utf-8")
        (out / "process_exit.txt").write_text(
            str(result.get("app_server_exit_code")) + "\n", encoding="ascii")
        (out / "runner_exit.txt").write_text(
            ("0\n" if str(result.get("disposition", "")).startswith("PASS_") else "1\n"),
            encoding="ascii")
        server.shutdown()
        server.server_close()

    print(json.dumps(result, indent=2))
    if not result["disposition"].startswith("PASS_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

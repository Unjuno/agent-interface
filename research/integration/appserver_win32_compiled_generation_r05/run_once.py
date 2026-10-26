"""One immutable AppServer -> compiled public-MCP -> supervised Win32 run."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "integration" / "standard_mcp_task_ledger_57_v1"),
                str(ROOT / "research" / "live_control")]

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.mcp_relay import Relay, PUBLIC_TOOLS
from runtime.cli_v1.supervised_win32_compiled import run_public_compiled
from runtime.core_v1.compiled_gui import validate as validate_interface
from runtime.core_v1.contract import validate_program
from runtime.backends.win32_v1.fixture_app import main as _fixture_import_guard  # noqa: F401
from research.integration.standard_mcp_task_ledger_57_v1.app_server_provider_to_public_mcp_v1 import (
    AppServerPublicMcpModelCall,
    parse_app_server_tool_request,
)
from research.integration.standard_mcp_task_ledger_57_v1.ledger import summarize
from research.integration.standard_mcp_task_ledger_57_v1.provider_attempt_recorder import ProviderAttemptRecorder
from research.integration.standard_mcp_task_ledger_57_v1.recorded_integrated_efficiency_model_call_v1 import build_model_provider_call
from research.integration.standard_mcp_task_ledger_57_v1.recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller
from codex_app_server_client_v2 import CodexAppServerClient
from persistent_planner_adapter_v2 import PersistentPlannerAdapter

COND = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
MODEL = COND["model"]
EFFORT = COND["effort"]
TASK = COND["task"]
REGION = COND["protocol"]["region"]
ORACLE_ID = TASK["oracle_id"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                               allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def mcp_reply(body: dict):
    """Adapt one retained public Relay text result to the caller's MCP shape."""
    return SimpleNamespace(content=[SimpleNamespace(text=json.dumps(body))])


def relay_body(envelope: dict) -> dict:
    if envelope.get("status") != "returned":
        raise RuntimeError("standard MCP call was not returned")
    rows = [item.get("text") for item in envelope.get("result", {}).get("content", [])
            if item.get("type") == "text" and isinstance(item.get("text"), str)]
    if len(rows) != 1:
        raise RuntimeError("standard MCP call did not return exactly one JSON text row")
    value = json.loads(rows[0])
    if not isinstance(value, dict):
        raise RuntimeError("standard MCP result body was not an object")
    return value


def raw_report(reply) -> dict:
    rows = [getattr(item, "text", None) for item in getattr(reply, "content", [])]
    for text in rows:
        if isinstance(text, str):
            value = json.loads(text)
            receipt = value.get("receipt")
            source = receipt.get("source") if isinstance(receipt, dict) else None
            raw = source.get("raw_report") if isinstance(source, dict) else None
            return raw if isinstance(raw, dict) else value
    raise RuntimeError("public MCP reply lacks a JSON report")


def strict_schema(value):
    if type(value) is dict:
        return {"type": "object", "properties": {key: strict_schema(item)
                for key, item in value.items()}, "required": list(value),
                "additionalProperties": False}
    if type(value) is int:
        return {"type": "integer"}
    raise TypeError("unsupported strict-schema example")


def appserver_command():
    codex = subprocess.run(["where.exe", "codex"], check=True, capture_output=True,
                           text=True).stdout.splitlines()[0].strip()
    command = [codex, "app-server", "--stdio"]
    for feature in ("apps", "plugins", "remote_plugin", "browser_use",
                    "browser_use_external", "computer_use", "in_app_browser",
                    "code_mode", "code_mode_host"):
        command += ["--disable", feature]
    for name in ("openaiDeveloperDocs", "node_repl"):
        command += ["-c", f"mcp_servers.{name}.enabled=false"]
    return command


def interface_spec():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "awcg-r05-win32-fixture-save",
        "session_scope": "one-owned-fixture-process",
        "surface": "fixture-window-client",
        "predicates": ["ready", "saved"],
        "symbols": {"fixture": {"kind": "target_reference",
            "target_reference": "fixture", "identity_predicate": "ready",
            "dependencies": ["ready"]}},
        "actions": {"save": {"target_symbol": "fixture",
            "operation": "click-type-save", "expected_effect": {"saved": True}}},
        "method": {"name": "one-grounded-click-and-save", "version": "1",
            "initial_state": "before", "max_transitions": 1,
            "max_runtime_ms": 10000,
            "states": {
                "before": {"branches": [{"when": {"ready": True,
                    "saved": False}, "outcome": "action", "action": "save",
                    "next_state": "after", "reason": None}]},
                "after": {"branches": [{"when": {"saved": True},
                    "outcome": "complete", "action": None,
                    "next_state": None, "reason": None}]}}},
    }


async def run():
    if RUN.exists():
        raise FileExistsError(f"immutable output path already exists: {RUN}")
    RUN.mkdir(parents=True)
    fixture_out = RUN / "fixture"
    fixture_out.mkdir()
    server_root = RUN / "server"
    server_root.mkdir()
    workspace = RUN / "empty-workspace"
    workspace.mkdir()
    app_dir = RUN / "app-server"
    app_dir.mkdir()
    protocol_journal = app_dir / "protocol.jsonl"
    effect_path = fixture_out / "effect.json"
    event_path = fixture_out / "events.jsonl"
    meta_path = fixture_out / "meta.json"
    fixture_cmd = [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
                   "--meta", str(meta_path), "--effect", str(effect_path),
                   "--events", str(event_path)]
    save_json(RUN / "invocation.json", {
        "attempt_id": COND["attempt_id"], "source_commit": COND["source_commit"],
        "conditions_sha256": sha((PACKET / "conditions.json").read_bytes()),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "python": sys.version, "model": MODEL, "effort": EFFORT,
        "fixture_command": fixture_cmd, "cwd": str(ROOT),
        "session_mode": "supervised-win32", "wslc_used": False,
        "docker_used": False, "started_unix_ns": time.time_ns(),
    })
    original_foreground = 0
    fixture = None
    client = planner = server = None
    terminal = {"attempt_id": COND["attempt_id"], "classification": "FAIL_OR_UNKNOWN",
                "wslc_used": False, "docker_used": False}
    run_error = None
    started = time.perf_counter_ns()

    import ctypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    original_foreground = int(user32.GetForegroundWindow() or 0)
    try:
        fixture = subprocess.Popen(fixture_cmd, cwd=ROOT,
            stdout=(fixture_out / "stdout.bin").open("wb"),
            stderr=(fixture_out / "stderr.bin").open("wb"))
        deadline = time.monotonic() + 10
        while not meta_path.exists() and fixture.poll() is None and time.monotonic() < deadline:
            await asyncio.sleep(.05)
        if fixture.poll() is not None or not meta_path.exists():
            raise RuntimeError("owned fixture did not become ready")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        hwnd = meta.get("hwnd")
        if type(hwnd) is not int or hwnd <= 0 or not user32.IsWindow(ctypes.c_void_p(hwnd)):
            raise RuntimeError("fixture metadata did not identify a live native HWND")
        save_json(RUN / "target-ownership.json", {
            "process_id": fixture.pid, "hwnd": hwnd,
            "window_title": "Agent Interface Win32 Fixture",
            "client_region": REGION,
            "owned_process_command": fixture_cmd,
        })

        class ServerClient:
            async def call_tool(self, name, arguments):
                return await server.call_tool(name, arguments)

        oracle_calls = []
        def independent_oracle(action):
            oracle_calls.append(dict(action))
            if not effect_path.exists():
                outcome = "failure"
                evidence_digest = sha(b"missing-effect-file")
            else:
                raw = effect_path.read_bytes()
                effect = json.loads(raw)
                evidence_digest = sha(raw)
                outcome = "success" if effect == TASK["independent_effect"] else "failure"
            return {"call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": ORACLE_ID, "outcome": outcome,
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": f"owned-win32-fixture-effect:sha256:{evidence_digest}"}

        server = create_server({"fixture": hwnd}, server_root,
            display_name="Agent Interface Win32 Fixture",
            session_mode="supervised-win32",
            supervised_win32_task_oracle=independent_oracle)
        recorder = ProviderAttemptRecorder(RUN / "ledger")
        relay = Relay(ServerClient(), tools=tuple(PUBLIC_TOOLS) + ("interface_verify_task",))
        caller = RecordedPublicMcpCaller(relay, recorder)

        grounding_request = {"id": relay.next_id, "tool": "interface_observe",
            "arguments": {"target": "fixture", "frame": "window_client",
                "region": REGION}}
        grounding_request_bytes = json.dumps(grounding_request, allow_nan=False,
            separators=(",", ":"), sort_keys=True).encode("utf-8")
        grounding_env = await relay.request(grounding_request_bytes)
        grounding_response_bytes = json.dumps(grounding_env, allow_nan=False,
            separators=(",", ":"), sort_keys=True).encode("utf-8")
        preprovider_dir = RUN / "grounding-public-mcp"
        preprovider_dir.mkdir()
        (preprovider_dir / "request.bin").write_bytes(grounding_request_bytes)
        (preprovider_dir / "response.bin").write_bytes(grounding_response_bytes)
        save_json(preprovider_dir / "receipt.json", {
            "attempt_id": COND["attempt_id"],
            "request_sha256": sha(grounding_request_bytes),
            "response_sha256": sha(grounding_response_bytes),
            "ledger_note": "Pre-provider grounding observation is retained separately because the task ledger enforces provider-before-tool ordering."})
        grounding_body = relay_body(grounding_env)
        report = raw_report(mcp_reply(grounding_body))
        generation = report.get("target_generation")
        observation_target = (report.get("observation", {}).get("target")
                              if isinstance(report.get("observation"), dict) else None)
        observed_target = report.get("target", observation_target)
        if (not isinstance(generation, str) or len(generation) != 64 or
                report.get("target_generation_consistency") != "matched" or
                report.get("status") != "returned" or observed_target != "fixture"):
            raise RuntimeError("fresh grounding observation lacked a matched target generation")
        int(generation, 16)
        save_json(RUN / "grounding-observation.json", {
            "call_id": grounding_env.get("id"), "target_generation": generation,
            "report": report, "envelope": grounding_env})
        content = grounding_env.get("result", {}).get("content", [])
        images = [item for item in content if item.get("type") == "image"]
        if len(images) != 1 or images[0].get("mimeType") != "image/png":
            raise RuntimeError("grounding observation did not provide one PNG image")
        image_bytes = base64.b64decode(images[0]["data"], validate=True)
        image_path = RUN / "grounding.png"
        image_path.write_bytes(image_bytes)
        from PIL import Image
        with Image.open(image_path) as shot:
            dimensions = list(shot.size)
        if dimensions != [REGION[2], REGION[3]]:
            raise RuntimeError(f"grounding image dimensions do not match frozen region: {dimensions}")

        command = appserver_command()
        save_json(app_dir / "invocation.json", {
            "command": command, "cwd": str(workspace), "model": MODEL,
            "effort": EFFORT, "disable_features": True,
        })
        client = CodexAppServerClient(command, cwd=workspace,
                                      journal_path=protocol_journal)
        initialize = client.initialize(name="agent-interface-awcg-r05", version="1")
        save_json(app_dir / "initialize.json", initialize)
        planner = PersistentPlannerAdapter(client, model=MODEL, effort=EFFORT,
            cwd=str(workspace), base_instructions=(
                "Return only the JSON object requested by the user and match the supplied schema. "
                "Do not invoke tools or add explanation."))
        thread_id = planner.start_session()
        save_json(app_dir / "thread-started.json", {"thread_id": thread_id})
        output_example = {"x": 100, "y": 60}
        model = AppServerPublicMcpModelCall(planner, protocol_journal,
            workspace=workspace, contract="win32-grounded-coordinate-v1",
            output_schema=strict_schema(output_example), model=MODEL,
            effort=EFFORT, path_converter=str, turn_timeout=90)
        prompt = (TASK["instruction"] + "\nImage coordinate origin is the top-left of the supplied "
            "400x180 window-client screenshot. Return x and y as integers.\n"
            "The allowed bounding box is x=24..300 inclusive and y=24..150 inclusive.")
        request_bytes, provider_call = build_model_provider_call(
            model_call=model.call, root=RUN / "provider-call", prompt=prompt,
            image=image_path, contract="win32-grounded-coordinate-v1", workspace=workspace)
        generation_record = await caller.invoke_provider(
            "appserver-win32-coordinate-r05", request_bytes, provider_call)
        save_json(RUN / "provider-terminal.json", {
            key: value for key, value in generation_record.items()
            if key != "response_bytes" and key != "backend_result"})
        if generation_record.get("status") != "completed":
            raise RuntimeError("AppServer provider turn did not complete")
        backend = generation_record.get("backend_result")
        answer = parse_app_server_tool_request(generation_record["response_bytes"],
            thread_id=backend["thread_id"], turn_id=backend["turn_id"])
        x, y = answer.get("x"), answer.get("y")
        bounds = COND["protocol"]["allowed_model_coordinate"]
        if (type(x) is not int or type(y) is not int or
                not bounds["x"][0] <= x <= bounds["x"][1] or
                not bounds["y"][0] <= y <= bounds["y"][1]):
            raise RuntimeError("model coordinate was outside the frozen fixture-only bounds")
        save_json(RUN / "model-coordinate.json", {
            "answer": answer, "bounds": bounds,
            "provider_attempt_id": "appserver-win32-coordinate-r05"})

        interface = interface_spec()
        validate_interface(interface)
        program = {"schema": "agent-interface/program-v1",
            "program_id": "awcg-r05-template",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": generation}},
            "authority": {"lease_id": "awcg-r05-template-lease",
                "expires_at_ns": time.monotonic_ns() + 20_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "pointer_move", "frame": "window_client", "x": x, "y": y},
                {"op": "pointer_button", "button": "left", "down": True},
                {"op": "pointer_button", "button": "left", "down": False},
                {"op": "wait_update", "timeout_ms": 100},
                {"op": "text", "text": "office"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"}]}
        validate_program(program)

        loop = asyncio.get_running_loop()
        action_return_ns = {"value": None}
        def observe(target, frame, region):
            envelope = asyncio.run_coroutine_threadsafe(caller.call_tool(
                "appserver-win32-coordinate-r05", "compiled-observe-" + str(relay.next_id),
                "interface_observe", {"target": target, "frame": frame,
                    "region": region}), loop).result(timeout=20)
            if envelope.get("status") != "returned":
                raise RuntimeError("compiled standard observation failed")
            return mcp_reply(relay_body(envelope))
        def dispatch(program_to_send, sequence, binding_revision):
            envelope = asyncio.run_coroutine_threadsafe(caller.call_tool(
                "appserver-win32-coordinate-r05", "compiled-dispatch-" + str(relay.next_id),
                "interface_dispatch", {"program": program_to_send,
                    "current_observation_seq": sequence,
                    "current_binding_revision": binding_revision,
                    "wait_for_result_ms": 10000}), loop).result(timeout=20)
            action_return_ns["value"] = time.monotonic_ns()
            if envelope.get("status") != "returned":
                raise RuntimeError("compiled standard dispatch failed")
            return mcp_reply(relay_body(envelope))
        def perceive(_report, _reply):
            saved = False
            if effect_path.exists():
                try:
                    saved = json.loads(effect_path.read_text(encoding="utf-8")) == TASK["independent_effect"]
                except (OSError, ValueError):
                    saved = False
            return {"ready": True, "saved": saved}
        def verify_effect(request, post_report, _reply):
            observed = (post_report.get("observation") or {}).get("capture_started_ns")
            returned = action_return_ns["value"]
            exact = False
            effect_digest = None
            if effect_path.exists():
                raw = effect_path.read_bytes()
                effect_digest = sha(raw)
                exact = json.loads(raw) == TASK["independent_effect"]
            fresh = (type(observed) is int and type(returned) is int and observed >= returned)
            return {"status": "succeeded" if exact and fresh else "failed",
                "evidence_ref": ("fixture-effect-sha256:" + effect_digest)
                    if exact and effect_digest else "fixture-effect-missing-or-mismatch",
                "post_observation_fresh_after_dispatch_return": fresh,
                "task_success": None}

        receipt = await asyncio.to_thread(run_public_compiled, interface,
            {"save": program}, target="fixture", current_binding_revision=1,
            region=REGION, observe=observe, dispatch=dispatch,
            perceive=perceive, verify_effect=verify_effect,
            expected_generation=generation, cancelled=lambda: False)
        save_json(RUN / "compiled-receipt.json", receipt)
        if receipt.get("standard_action_call_ids") and len(receipt["standard_action_call_ids"]) == 1:
            action_call_id = receipt["standard_action_call_ids"][0]
        else:
            raise RuntimeError("compiled caller did not retain exactly one action call id")
        if receipt.get("standard_observation_call_ids") is None:
            raise RuntimeError("compiled caller omitted standard observation call ids")

        verify_envelope = await caller.call_tool("appserver-win32-coordinate-r05",
            "task-oracle-" + relay.next_id.to_bytes(16, "big").hex(),
            "interface_verify_task", {"call_id": action_call_id,
                "wait_for_result_ms": 3000})
        verify_body = relay_body(verify_envelope)
        save_json(RUN / "task-oracle.json", verify_body)
        observed_effect = (json.loads(effect_path.read_text(encoding="utf-8"))
                           if effect_path.exists() else None)
        score = bool(
            generation_record.get("usage", {}).get("status") == "reported" and
            type(answer.get("x")) is int and type(answer.get("y")) is int and
            receipt.get("outcome") == "TASK_SUCCEEDED" and
            receipt.get("completed_transitions") == 1 and
            len(receipt.get("standard_action_call_ids", [])) == 1 and
            bool(receipt.get("standard_observation_call_ids")) and
            observed_effect == TASK["independent_effect"] and
            verify_body.get("status") == "verified" and
            verify_body.get("task_success") is True and
            (verify_body.get("task_effect", {}).get("receipt", {}).get("call_id") == action_call_id) and
            (verify_body.get("task_effect", {}).get("receipt", {}).get("target_generation") == generation))
        recorder.record_task_score("awcg-r05-server-task-oracle", score,
            (effect_path.read_bytes() if effect_path.exists() else b"missing-effect-file"))
        ledger = recorder.reconcile()
        save_json(RUN / "ledger-reconciled.json", ledger)
        terminal = {"attempt_id": COND["attempt_id"],
            "classification": "PASS_SCOPED_WIN32_COMPILED_LIVE" if score and ledger.get("complete") else "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED",
            "model": MODEL, "effort": EFFORT,
            "provider_status": generation_record.get("status"),
            "usage": generation_record.get("usage"),
            "coordinate": answer, "grounding_target_generation": generation,
            "compiled_outcome": receipt.get("outcome"),
            "input_dispatched_call_ids": receipt.get("standard_action_call_ids"),
            "standard_observation_call_ids": receipt.get("standard_observation_call_ids"),
            "task_oracle_status": verify_body.get("status"),
            "independent_task_success": verify_body.get("task_success"),
            "fixture_effect": observed_effect,
            "release": next((event.get("release") for event in receipt.get("critical_events", [])
                             if event.get("event") == "action_terminal"), None),
            "ledger_complete": ledger.get("complete"),
            "ledger_summary": summarize(ledger.get("events", [])),
            "efficiency_claim": None,
            "elapsed_ns": time.perf_counter_ns() - started,
            "wslc_used": False, "docker_used": False}
        save_json(RUN / "result.json", terminal)
        if not score or not ledger.get("complete"):
            raise RuntimeError("frozen AWCG-R01 pass criteria were not all met")
    except BaseException as exc:
        run_error = exc
        terminal.update({"error_type": type(exc).__name__, "error": str(exc),
            "elapsed_ns": time.perf_counter_ns() - started})
        save_json(RUN / "result.json", terminal)
    finally:
        if server is not None:
            try:
                close = await server.call_tool("interface_close", {})
                save_json(RUN / "server-close.json", close.model_dump(mode="json"))
            except BaseException as exc:
                save_json(RUN / "server-close-error.json", {"type": type(exc).__name__, "message": str(exc)})
        if client is not None:
            try:
                client.close(timeout=5)
            except BaseException as exc:
                save_json(RUN / "appserver-close-error.json", {"type": type(exc).__name__, "message": str(exc)})
        if fixture is not None and fixture.poll() is None:
            try:
                hwnd = json.loads(meta_path.read_text(encoding="utf-8"))["hwnd"]
                user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0010, 0, 0)
                fixture.wait(timeout=5)
            except BaseException:
                fixture.terminate()
                try:
                    fixture.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    fixture.kill()
                    fixture.wait(timeout=3)
        current_foreground = int(user32.GetForegroundWindow() or 0)
        restored = False
        if original_foreground and user32.IsWindow(ctypes.c_void_p(original_foreground)):
            restored = bool(user32.SetForegroundWindow(ctypes.c_void_p(original_foreground)))
        save_json(RUN / "cleanup.json", {
            "fixture_exit_code": None if fixture is None else fixture.poll(),
            "foreground_before": original_foreground,
            "foreground_at_cleanup": current_foreground,
            "foreground_restore_requested": restored,
            "foreground_after_restore": int(user32.GetForegroundWindow() or 0),
            "finished_unix_ns": time.time_ns()})
        rows = [f"{sha(path.read_bytes())}  {path.relative_to(RUN).as_posix()}"
                for path in sorted(RUN.rglob("*")) if path.is_file() and path.name != "SHA256SUMS"]
        (RUN / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    if run_error is not None:
        raise run_error
    print(json.dumps(terminal, sort_keys=True, indent=2))


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(run(), timeout=180))

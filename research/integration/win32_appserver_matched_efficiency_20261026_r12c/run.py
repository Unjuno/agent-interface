"""Counterbalanced live Win32 AppServer direct-versus-compiled study (R12)."""
import asyncio
import base64
import ctypes
import hashlib
import json
import subprocess
import sys
import time
import uuid
from ctypes import wintypes
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
CONDITIONS = json.loads((PACKET / "CONDITIONS.json").read_text(encoding="utf-8"))
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "live_control"),
    str(ROOT / "research" / "integration" / "standard_mcp_task_ledger_57_v1")]

from runtime.backends.win32_v1.backend import BUTTON_FLAGS, Win32Backend, virtual_key
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.supervised_win32_compiled import run_public_compiled
from runtime.cli_v1.win32_supervisor_helpers import create_native_win32_components
from runtime.core_v1.compiled_gui import validate as validate_interface
from runtime.core_v1.contract import validate_program
from app_server_provider_to_public_mcp_v1 import (
    AppServerPublicMcpModelCall, parse_app_server_tool_request)
from codex_app_server_client_v2 import CodexAppServerClient
from persistent_planner_adapter_v2 import PersistentPlannerAdapter
from recorded_integrated_efficiency_model_call_v1 import build_model_provider_call


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2,
        ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def public_body(reply):
    rows = [getattr(block, "text", None) for block in getattr(reply, "content", [])]
    rows = [row for row in rows if isinstance(row, str)]
    if len(rows) != 1:
        raise RuntimeError("standard MCP reply did not contain exactly one text row")
    return json.loads(rows[0])


def raw_report(body):
    receipt = body.get("receipt")
    source = receipt.get("source") if isinstance(receipt, dict) else None
    report = source.get("raw_report") if isinstance(source, dict) else None
    return report if isinstance(report, dict) else body


def strict_schema(value):
    if type(value) is dict:
        return {"type": "object", "properties": {k: strict_schema(v)
            for k, v in value.items()}, "required": list(value),
            "additionalProperties": False}
    if type(value) is bool:
        return {"type": "boolean"}
    if type(value) is int:
        return {"type": "integer"}
    raise TypeError("unsupported schema example")


def appserver_command():
    codex = subprocess.run(["where.exe", "codex"], check=True,
        capture_output=True, text=True).stdout.splitlines()[0].strip()
    command = [codex, "app-server", "--stdio"]
    for feature in ("apps", "plugins", "remote_plugin", "browser_use",
                    "browser_use_external", "computer_use", "in_app_browser",
                    "code_mode", "code_mode_host"):
        command += ["--disable", feature]
    for name in ("openaiDeveloperDocs", "node_repl"):
        command += ["-c", f"mcp_servers.{name}.enabled=false"]
    return command


def input_state(hwnd):
    backend = Win32Backend({"fixture": hwnd})
    try:
        generation = backend.target_generation("fixture")
        states, witnesses = {}, {}
        for name, vk in (("SHIFT", virtual_key("SHIFT")),
                         ("CTRL", virtual_key("CTRL")),
                         ("S", virtual_key("S")),
                         ("left_button", BUTTON_FLAGS["left"][2])):
            states[name] = backend._key_down_state(vk, "fixture")
            witnesses[name] = list(backend._last_state_query_witness)
        return {"target_generation": generation, "states": states,
            "state_query_witnesses": witnesses,
            "observed_monotonic_ns": time.monotonic_ns()}
    finally:
        backend.close()


def compiled_interface():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "win32-r12-two-stage-save",
        "session_scope": "one-owned-fixture-process",
        "surface": "fixture-window-client",
        "predicates": ["ready", "clicked", "typed", "saved"],
        "symbols": {"fixture": {"kind": "target_reference",
            "target_reference": "fixture", "identity_predicate": "ready",
            "dependencies": ["ready"]}},
        "actions": {
            "enter_text": {"target_symbol": "fixture", "operation": "click-and-type",
                "expected_effect": {"clicked": True, "typed": True}},
            "save": {"target_symbol": "fixture", "operation": "save",
                "expected_effect": {"saved": True}}},
        "method": {"name": "model-grounded-two-stage-save", "version": "1",
            "initial_state": "before", "max_transitions": 2,
            "max_runtime_ms": 10000,
            "states": {
                "before": {"branches": [{"when": {"ready": True,
                    "clicked": False, "typed": False}, "outcome": "action",
                    "action": "enter_text", "next_state": "after_entry", "reason": None}]},
                "after_entry": {"branches": [{"when": {"clicked": True,
                    "typed": True, "saved": False}, "outcome": "action",
                    "action": "save", "next_state": "after_save", "reason": None}]},
                "after_save": {"branches": [{"when": {"saved": True},
                    "outcome": "complete", "action": None,
                    "next_state": None, "reason": None}]}}}}


async def run_model_turn(planner, protocol_journal, workspace, image_path,
        prompt, schema_example, turn_root, contract):
    model_call = AppServerPublicMcpModelCall(planner, protocol_journal,
        workspace=workspace, contract=contract,
        output_schema=strict_schema(schema_example), model=CONDITIONS["model"],
        effort=CONDITIONS["effort"], path_converter=str, turn_timeout=90)
    request_bytes, provider_call = build_model_provider_call(
        model_call=model_call.call, root=turn_root, prompt=prompt,
        image=image_path, contract=contract, workspace=workspace)
    turn_root = Path(turn_root)
    turn_root.parent.mkdir(parents=True, exist_ok=True)
    (turn_root.parent / (turn_root.name + ".request.bin")).write_bytes(request_bytes)
    started = time.monotonic_ns()
    generation = await provider_call()
    returned = time.monotonic_ns()
    save(turn_root / "provider-terminal.json", {key: value for key, value
        in generation.items() if key not in {"response_bytes", "backend_result"}})
    if generation.get("status") != "completed":
        raise RuntimeError("AppServer model turn did not complete")
    backend = generation.get("backend_result") or {}
    response_bytes = generation.get("response_bytes")
    (turn_root / "response.jsonl").write_bytes(response_bytes)
    answer = parse_app_server_tool_request(response_bytes,
        thread_id=backend["thread_id"], turn_id=backend["turn_id"])
    usage = generation.get("usage") or {}
    backend_usage = backend.get("usage") or {}
    normalized_match = (usage.get("status") == "reported" and
        all(usage.get(key) == value for key, value in backend_usage.items()))
    result = {"status": generation["status"], "answer": answer,
        "usage": usage, "backend_usage": backend_usage,
        "usage_matches_journal_fields": normalized_match,
        "thread_id": backend.get("thread_id"), "turn_id": backend.get("turn_id"),
        "started_monotonic_ns": started, "returned_monotonic_ns": returned,
        "latency_ns": returned - started,
        "requested_model": CONDITIONS["model"], "requested_effort": CONDITIONS["effort"],
        "contract": contract}
    save(turn_root / "result.json", result)
    return result


async def run_cell(cell_spec):
    cell_id = cell_spec["cell_id"]
    arm = cell_spec["arm"]
    cell_root = RUN / "cells" / cell_id
    cell_root.mkdir(parents=True, exist_ok=False)
    fixture_dir = cell_root / "fixture"
    server_dir = cell_root / "server"
    model_dir = cell_root / "model"
    workspace = cell_root / "empty-workspace"
    for path in (fixture_dir, server_dir, model_dir, workspace):
        path.mkdir()
    meta_path, effect_path, events_path = (fixture_dir / "meta.json",
        fixture_dir / "effect.json", fixture_dir / "events.jsonl")
    fixture_cmd = [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
        "--meta", str(meta_path), "--effect", str(effect_path), "--events", str(events_path)]
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
        wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    foreground_before = int(user32.GetForegroundWindow() or 0)
    fixture = None
    server = None
    appserver = None
    outcome = {"cell_id": cell_id, "pair": cell_spec["pair"], "arm": arm,
        "status": "FAIL_OR_UNKNOWN", "wslc_used": False, "docker_used": False,
        "python_version": sys.version}
    tool_calls = []
    provider_turns = []
    dispatch_rows = []
    cell_started = None
    try:
        fixture = subprocess.Popen(fixture_cmd, cwd=ROOT,
            stdout=(fixture_dir / "stdout.bin").open("wb"),
            stderr=(fixture_dir / "stderr.bin").open("wb"))
        deadline = time.monotonic() + 10
        while not meta_path.exists() and fixture.poll() is None and time.monotonic() < deadline:
            await asyncio.sleep(.05)
        if fixture.poll() is not None or not meta_path.exists():
            raise RuntimeError("owned Win32 fixture did not become ready")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        hwnd = meta.get("hwnd")
        if type(hwnd) is not int or hwnd <= 0 or not user32.IsWindow(ctypes.c_void_p(hwnd)):
            raise RuntimeError("fixture metadata does not identify its owned live HWND")
        native_preflight = input_state(hwnd)
        if any(native_preflight["states"].values()):
            raise RuntimeError("fixture began with a tracked input down; no study action started")
        outcome.update({"fixture_pid": fixture.pid, "hwnd": hwnd,
            "target_generation": native_preflight["target_generation"],
            "native_preflight": native_preflight})
        save(cell_root / "ownership.json", {"pid": fixture.pid, "hwnd": hwnd,
            "command": fixture_cmd, "generation": native_preflight["target_generation"]})
        expected = CONDITIONS["task"]["effect"]
        oracle_id = CONDITIONS["task"]["oracle_ids"][int(cell_spec["index"])]

        def task_oracle(action):
            raw = effect_path.read_bytes() if effect_path.is_file() else b"missing-effect-file"
            try:
                effect = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                effect = None
            return {"call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": oracle_id,
                "outcome": "success" if effect == expected else "failure",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-effect:sha256:" + sha(raw)}

        owner_factory = lambda targets, root, _display: create_native_win32_components(targets, root)[0]
        server = create_server({"fixture": hwnd}, server_dir,
            display_name="Agent Interface Win32 R12 fixture",
            session_mode="supervised-win32", supervised_win32_task_oracle=task_oracle,
            _supervised_win32_owner_factory=owner_factory,
            _supervised_win32_producer_factory=lambda configured, root, _display: create_native_win32_components(configured, root)[1])
        app_dir = model_dir / "app-server"
        app_dir.mkdir()
        protocol_journal = app_dir / "protocol.jsonl"
        command = appserver_command()
        save(app_dir / "invocation.json", {"command": command,
            "cwd": str(workspace), "model": CONDITIONS["model"],
            "effort": CONDITIONS["effort"], "sandbox": "read-only"})
        appserver = CodexAppServerClient(command, cwd=workspace,
            journal_path=protocol_journal)
        save(app_dir / "initialize.json", appserver.initialize(
            name="agent-interface-r12", version="1"))
        planner = PersistentPlannerAdapter(appserver, model=CONDITIONS["model"],
            effort=CONDITIONS["effort"], cwd=str(workspace), base_instructions=(
                "Return only the JSON object requested by the user and match the supplied schema. "
                "Do not invoke tools or add explanation."))
        thread_id = planner.start_session()
        save(app_dir / "thread-started.json", {"thread_id": thread_id})

        public_observation_sequence = 0

        async def observe(note, save_image=False):
            nonlocal public_observation_sequence
            public_observation_sequence += 1
            started = time.monotonic_ns()
            reply = await server.call_tool("interface_observe", {"target": "fixture",
                "frame": "window_client", "region": CONDITIONS["task"]["public_region"]})
            returned = time.monotonic_ns()
            body = public_body(reply)
            report = raw_report(body)
            call_id = body.get("call_id") or report.get("call_id")
            row = {"kind": "observation", "note": note, "call_id": call_id,
                "started_monotonic_ns": started, "returned_monotonic_ns": returned,
                "target_generation": report.get("target_generation"),
                "capture_started_ns": (report.get("observation") or {}).get("capture_started_ns"),
                "sequence": public_observation_sequence,
                "status": report.get("status")}
            if report.get("target_generation") != native_preflight["target_generation"]:
                raise RuntimeError("target generation changed during a study cell")
            if save_image:
                images = [block for block in reply.content
                    if getattr(block, "type", None) == "image"]
                if len(images) != 1 or not isinstance(getattr(images[0], "data", None), str):
                    raise RuntimeError("fresh public observation did not return exactly one image")
                image_path = cell_root / "observations" / f"{note}.png"
                image_path.parent.mkdir(exist_ok=True)
                image_path.write_bytes(base64.b64decode(images[0].data, validate=True))
                from PIL import Image
                with Image.open(image_path) as image:
                    row["image_dimensions"] = list(image.size)
                if row["image_dimensions"] != [400, 180]:
                    raise RuntimeError("observation image did not match the frozen screen region")
                row["image_sha256"] = sha(image_path.read_bytes())
                row["image_path"] = image_path.relative_to(cell_root).as_posix()
            tool_calls.append(row)
            save(cell_root / "observations" / f"{note}.json", {"body": body,
                "raw_report": report, "receipt": row})
            return reply, body, report, row

        async def dispatch(program, label, sequence):
            program = json.loads(json.dumps(program))
            program["source"]["observation_seq"] = sequence
            program["source"]["binding_revision"] = 1
            program["source"]["target_generations"] = {"fixture": native_preflight["target_generation"]}
            program["program_id"] = "r12-" + label + "-" + uuid.uuid4().hex
            program["authority"]["lease_id"] = "r12-" + uuid.uuid4().hex
            program["authority"]["expires_at_ns"] = time.monotonic_ns() + 20_000_000_000
            validate_program(program)
            started = time.monotonic_ns()
            reply = await server.call_tool("interface_dispatch", {
                "program": program, "current_observation_seq": sequence,
                "current_binding_revision": 1, "wait_for_result_ms": 15000})
            returned = time.monotonic_ns()
            body = public_body(reply)
            report = raw_report(body)
            call_id = body.get("call_id") or report.get("call_id")
            save(cell_root / "dispatches" / f"{label}-response.json", {
                "body": body, "raw_report": report,
                "is_error": bool(getattr(reply, "isError", False)),
                "returned_monotonic_ns": returned})
            if not isinstance(call_id, str):
                raise RuntimeError("standard dispatch response had no public call id; full response retained")
            result_reply = await server.call_tool("interface_results", {"call_id": call_id})
            result_body = public_body(result_reply)
            action = result_body.get("action") or {}
            row = {"kind": "dispatch", "label": label, "call_id": call_id,
                "operation_id": action.get("operation_id") or report.get("operation_id"),
                "program": program, "started_monotonic_ns": started,
                "returned_monotonic_ns": returned,
                "release_confirmed": action.get("release_confirmed"),
                "target_generation": action.get("target_generation") or report.get("target_generation"),
                "status": report.get("status"), "input_dispatched": report.get("input_dispatched")}
            tool_calls.append(row)
            tool_calls.append({"kind": "results", "label": label,
                "call_id": call_id, "returned_monotonic_ns": time.monotonic_ns()})
            dispatch_rows.append(row)
            save(cell_root / "dispatches" / f"{label}.json", {"body": body,
                "raw_report": report, "retained_result": result_body, "receipt": row})
            return reply, body, report, result_body, row

        async def model_turn(turn_label, image_path, prompt, schema_example):
            contract = f"win32-r12-{cell_id}-{turn_label}"
            result = await run_model_turn(planner, protocol_journal, workspace,
                image_path, prompt, schema_example,
                cell_root / "provider" / turn_label, contract)
            provider_turns.append(result)
            tool_calls.append({"kind": "provider", "turn": turn_label,
                "started_monotonic_ns": result["started_monotonic_ns"],
                "returned_monotonic_ns": result["returned_monotonic_ns"],
                "latency_ns": result["latency_ns"]})
            return result

        first_observation, first_body, first_report, first_row = await observe("initial-grounding", True)
        cell_started = first_row["started_monotonic_ns"]
        if first_row["target_generation"] != native_preflight["target_generation"]:
            raise RuntimeError("initial model observation did not match native target generation")
        first_image = cell_root / "observations" / "initial-grounding.png"
        prompt1 = CONDITIONS["task"]["initial_model_prompt"]
        turn1 = await model_turn("turn1-coordinate", first_image, prompt1, {"x": 100, "y": 60})
        answer = turn1["answer"]
        bounds = CONDITIONS["task"]["coordinate_bounds"]
        if (type(answer.get("x")) is not int or type(answer.get("y")) is not int
                or not bounds["x"][0] <= answer["x"] <= bounds["x"][1]
                or not bounds["y"][0] <= answer["y"] <= bounds["y"][1]):
            raise RuntimeError("model coordinate outside preregistered bounds; no action submitted")
        outcome["model_coordinate"] = answer
        outcome["grounding_generation"] = first_row["target_generation"]

        stage1 = {"schema": "agent-interface/program-v1", "program_id": "r12-stage1",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": native_preflight["target_generation"]}},
            "authority": {"lease_id": "r12-stage1", "expires_at_ns": time.monotonic_ns() + 20_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "pointer_move", "frame": "window_client", "x": answer["x"], "y": answer["y"]},
                {"op": "pointer_button", "button": "left", "down": True},
                {"op": "pointer_button", "button": "left", "down": False},
                {"op": "wait_update", "timeout_ms": 100},
                {"op": "text", "text": "office"}, {"op": "release_all"}]}
        stage2 = {"schema": "agent-interface/program-v1", "program_id": "r12-stage2",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": native_preflight["target_generation"]}},
            "authority": {"lease_id": "r12-stage2", "expires_at_ns": time.monotonic_ns() + 20_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL", "S"]}, {"op": "release_all"}]}

        if arm == "direct":
            fresh1, _body, report1, row1 = await observe("direct-pre-stage1", False)
            if row1["target_generation"] != native_preflight["target_generation"]:
                raise RuntimeError("direct path target generation changed during model wait")
            action1 = await dispatch(stage1, "direct-enter-text", (report1.get("observation") or {}).get("sequence", 1))
            if action1[4]["release_confirmed"] is not True:
                raise RuntimeError("direct stage-one action did not confirm input release")
            typed_events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            if [event.get("code") for event in typed_events if event.get("kind") == "char"] != list(map(ord, "office")):
                raise RuntimeError("direct stage-one text events did not match office")
            text_observation, _body, text_report, text_row = await observe("direct-post-entry", True)
            if type(text_row["capture_started_ns"]) is not int or text_row["capture_started_ns"] <= action1[4]["returned_monotonic_ns"]:
                raise RuntimeError("direct stage-one observation was not fresh after action response")
            second_image = cell_root / "observations" / "direct-post-entry.png"
            turn2 = await model_turn("turn2-save-decision", second_image,
                CONDITIONS["task"]["direct_second_model_prompt"], {"save": True})
            if turn2["answer"].get("save") is not True:
                raise RuntimeError("direct second model decision did not authorize save")
            fresh2, _body, report2, row2 = await observe("direct-pre-save", False)
            if row2["target_generation"] != text_row["target_generation"]:
                raise RuntimeError("direct target generation changed during second model wait")
            action2 = await dispatch(stage2, "direct-save", (report2.get("observation") or {}).get("sequence", 1))
            if action2[4]["release_confirmed"] is not True:
                raise RuntimeError("direct save action did not confirm input release")
            post_reply, post_body, post_report, post_row = await observe("direct-post-save", False)
            exact_effect = effect_path.is_file() and json.loads(effect_path.read_text(encoding="utf-8")) == expected
            post_capture = post_row.get("capture_started_ns")
            post_dispatch_return = action2[4]["returned_monotonic_ns"]
            direct_effect_timing = {"status": "succeeded" if exact_effect and
                type(post_capture) is int and post_capture > post_dispatch_return else "failed",
                "post_observation_capture_started_ns": post_capture,
                "dispatch_response_returned_ns": post_dispatch_return,
                "post_observation_fresh_after_dispatch_response": (
                    type(post_capture) is int and post_capture > post_dispatch_return)}
            save(cell_root / "effect-verification-audit.json", direct_effect_timing)
            outcome["terminal_call_id"] = action2[4]["call_id"]
            outcome["arm_action_receipts"] = [action1[4], action2[4]]
            outcome["first_stage_observation"] = text_row
            outcome["post_action_observation"] = post_row
            outcome["direct_second_model_decision"] = turn2["answer"]
        elif arm == "compiled":
            interface = compiled_interface()
            validate_interface(interface)
            first_action_return = {"ns": None}
            compiled_observations = []
            compiled_receipts = []
            loop = asyncio.get_running_loop()

            def observe_callback(target, frame, region):
                fut = asyncio.run_coroutine_threadsafe(server.call_tool("interface_observe", {
                    "target": target, "frame": frame, "region": region}), loop)
                reply = fut.result(timeout=30)
                body = public_body(reply)
                report = raw_report(body)
                observation = report.get("observation") or {}
                row = {"target_generation": report.get("target_generation"),
                    "capture_started_ns": observation.get("capture_started_ns"),
                    "sequence": observation.get("sequence"), "call_id": body.get("call_id")}
                compiled_observations.append(row)
                tool_calls.append({"kind": "observation", "note": "compiled-core",
                    **row, "returned_monotonic_ns": time.monotonic_ns()})
                return reply

            def dispatch_callback(program, sequence, revision):
                label = "compiled-enter-text" if any(
                    op.get("op") == "text" for op in program.get("ops", [])) else "compiled-save"
                fut = asyncio.run_coroutine_threadsafe(server.call_tool("interface_dispatch", {
                    "program": program, "current_observation_seq": sequence,
                    "current_binding_revision": revision, "wait_for_result_ms": 15000}), loop)
                started = time.monotonic_ns()
                reply = fut.result(timeout=30)
                returned = time.monotonic_ns()
                body = public_body(reply)
                report = raw_report(body)
                save(cell_root / "dispatches" / f"{label}-response.json", {
                    "body": body, "raw_report": report,
                    "is_error": bool(getattr(reply, "isError", False)),
                    "returned_monotonic_ns": time.monotonic_ns()})
                call_id = body.get("call_id") or report.get("call_id")
                result_fut = asyncio.run_coroutine_threadsafe(server.call_tool(
                    "interface_results", {"call_id": call_id}), loop)
                result_body = public_body(result_fut.result(timeout=20))
                action = result_body.get("action") or {}
                row = {"kind": "dispatch", "label": label, "call_id": call_id,
                    "operation_id": action.get("operation_id"),
                    "release_confirmed": action.get("release_confirmed"),
                    "target_generation": action.get("target_generation"),
                    "started_monotonic_ns": started, "returned_monotonic_ns": returned,
                    "program": program, "status": report.get("status")}
                compiled_receipts.append(row)
                dispatch_rows.append(row)
                tool_calls.extend([row, {"kind": "results", "label": label,
                    "call_id": call_id, "returned_monotonic_ns": time.monotonic_ns()}])
                save(cell_root / "dispatches" / f"{label}.json", {"body": body,
                    "raw_report": report, "retained_result": result_body, "receipt": row})
                if label == "compiled-enter-text":
                    first_action_return["ns"] = returned
                return reply

            def perceive(_report, _reply):
                rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
                chars = [row.get("code") for row in rows if row.get("kind") == "char"]
                return {"ready": any(row.get("kind") == "ready" for row in rows),
                    "clicked": sum(row.get("kind") == "click" for row in rows) >= 1,
                    "typed": chars == list(map(ord, "office")),
                    "saved": effect_path.is_file() and json.loads(effect_path.read_text(encoding="utf-8")) == expected}

            def verify_effect(_request, post_report, _reply):
                started = (post_report.get("observation") or {}).get("capture_started_ns")
                returned = (compiled_receipts[-1].get("returned_monotonic_ns")
                    if compiled_receipts else None)
                exact = effect_path.is_file() and json.loads(effect_path.read_text(encoding="utf-8")) == expected
                fresh = type(started) is int and type(returned) is int and started > returned
                row = {"status": "succeeded" if exact and fresh else "failed",
                    "effect_sha256": sha(effect_path.read_bytes()) if effect_path.is_file() else None,
                    "post_observation_capture_started_ns": started,
                    "dispatch_response_returned_ns": returned,
                    "post_observation_fresh_after_dispatch_return": fresh}
                save(cell_root / "effect-verification-audit.json", row)
                return {"status": row["status"], "evidence_ref": row["effect_sha256"] or "missing-effect"}

            program1 = dict(stage1)
            program2 = dict(stage2)
            task_programs = {"enter_text": program1, "save": program2}
            receipt = await asyncio.to_thread(run_public_compiled, interface,
                task_programs, target="fixture", current_binding_revision=1,
                region=CONDITIONS["task"]["public_region"], observe=observe_callback,
                dispatch=dispatch_callback, perceive=perceive, verify_effect=verify_effect,
                expected_generation=native_preflight["target_generation"], cancelled=lambda: False)
            save(cell_root / "compiled-receipt.json", receipt)
            action_ids = receipt.get("standard_action_call_ids")
            if receipt.get("outcome") != "TASK_SUCCEEDED" or type(action_ids) is not list or len(action_ids) != 2:
                raise RuntimeError("compiled graph did not complete exactly two public actions")
            if len(compiled_receipts) != 2 or any(row.get("release_confirmed") is not True for row in compiled_receipts):
                raise RuntimeError("compiled graph action receipts did not confirm release")
            outcome["terminal_call_id"] = action_ids[-1]
            outcome["arm_action_receipts"] = compiled_receipts
            outcome["compiled_receipt"] = receipt
            outcome["compiled_observations"] = compiled_observations
            outcome["post_action_observation"] = {"capture_started_ns": (compiled_observations[-1] or {}).get("capture_started_ns")}
            outcome["first_stage_observation"] = next((row for row in compiled_observations
                if row.get("sequence") == 2), {})
        else:
            raise RuntimeError("unknown preregistered arm")

        oracle_started = time.monotonic_ns()
        oracle_reply = await server.call_tool("interface_verify_task", {
            "call_id": outcome["terminal_call_id"], "wait_for_result_ms": 3000})
        oracle_body = public_body(oracle_reply)
        oracle_returned = time.monotonic_ns()
        tool_calls.append({"kind": "oracle", "call_id": outcome["terminal_call_id"],
            "started_monotonic_ns": oracle_started, "returned_monotonic_ns": oracle_returned})
        save(cell_root / "task-oracle.json", oracle_body)
        terminal_result = await server.call_tool("interface_results", {
            "call_id": outcome["terminal_call_id"]})
        retained_body = public_body(terminal_result)
        save(cell_root / "terminal-retained-result.json", retained_body)
        native_after = input_state(hwnd)
        event_rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
        effect = json.loads(effect_path.read_text(encoding="utf-8")) if effect_path.is_file() else None
        action = retained_body.get("action") or {}
        receipt = ((oracle_body.get("task_effect") or {}).get("receipt") or {})
        effect_timing = json.loads((cell_root / "effect-verification-audit.json").read_text(encoding="utf-8")) if (cell_root / "effect-verification-audit.json").is_file() else {}
        if arm == "direct":
            fresh_effect = (effect == expected and effect_timing.get("post_observation_fresh_after_dispatch_response") is True)
        else:
            fresh_effect = (effect == expected and effect_timing.get("post_observation_fresh_after_dispatch_return") is True)
        checks = {
            "native_neutral_readback": native_after["target_generation"] == native_preflight["target_generation"] and all(value is False for value in native_after["states"].values()),
            "two_actions_confirmed_release": len(outcome["arm_action_receipts"]) == 2 and all(row.get("release_confirmed") is True for row in outcome["arm_action_receipts"]),
            "exact_task_effect_and_events": effect == expected and sum(row.get("kind") == "click" for row in event_rows) == 1 and [row.get("code") for row in event_rows if row.get("kind") == "char"] == list(map(ord, "office")) and sum(row.get("kind") == "save" for row in event_rows) == 1,
            "fresh_post_dispatch_observation": fresh_effect,
            "independent_task_oracle_exact_binding": oracle_body.get("status") == "verified" and oracle_body.get("task_success") is True and receipt.get("call_id") == outcome["terminal_call_id"] and receipt.get("operation_id") == action.get("operation_id") and receipt.get("target_generation") == native_preflight["target_generation"] and receipt.get("oracle_id") == oracle_id,
            "model_usage_fields_reconciled_to_protocol": len(provider_turns) == (2 if arm == "direct" else 1) and all(row["usage_matches_journal_fields"] for row in provider_turns),
            "appserver_generation_continuity": all(row.get("target_generation") == native_preflight["target_generation"] for row in tool_calls if row.get("kind") == "observation" and row.get("target_generation") is not None),
        }
        outcome.update({"status": "PASS" if all(checks.values()) else "FAIL_OR_UNKNOWN",
            "checks": checks, "effect": effect, "events": event_rows,
            "task_oracle": oracle_body, "terminal_retained_result": retained_body,
            "native_after": native_after, "standard_tool_calls": tool_calls,
            "provider_turns": provider_turns,
            "provider_turn_count": len(provider_turns),
            "reported_tokens": {key: sum((row.get("usage") or {}).get(key, 0)
                for row in provider_turns) for key in ("input_tokens", "output_tokens", "reasoning_output_tokens")},
            "elapsed_ns": oracle_returned - cell_started,
            "appserver_latency_ns": sum(row["latency_ns"] for row in provider_turns),
            "public_call_counts": {kind: sum(row.get("kind") == kind for row in tool_calls)
                for kind in ("observation", "dispatch", "results", "oracle")}})
    except BaseException as exc:
        outcome.update({"status": "FAIL_OR_UNKNOWN", "error_type": type(exc).__name__,
            "error": str(exc)[:1000]})
    finally:
        if server is not None:
            try:
                outcome["server_close"] = public_body(await server.call_tool("interface_close", {}))
            except BaseException as exc:
                outcome["server_close_error"] = repr(exc)
        if appserver is not None:
            try:
                appserver.close(timeout=5)
                outcome["appserver_closed"] = True
            except BaseException as exc:
                outcome["appserver_closed"] = False
                outcome["appserver_close_error"] = repr(exc)
        if fixture is not None and fixture.poll() is None:
            try:
                hwnd_now = json.loads(meta_path.read_text(encoding="utf-8"))["hwnd"]
                user32.PostMessageW(ctypes.c_void_p(hwnd_now), 0x0010, 0, 0)
                fixture.wait(timeout=5)
            except BaseException as exc:
                outcome["fixture_close_error"] = repr(exc)
                try:
                    fixture.terminate()
                    fixture.wait(timeout=3)
                except BaseException:
                    try:
                        fixture.kill()
                        fixture.wait(timeout=3)
                    except BaseException:
                        pass
        before_restore = int(user32.GetForegroundWindow() or 0)
        if foreground_before and user32.IsWindow(ctypes.c_void_p(foreground_before)):
            user32.SetForegroundWindow(ctypes.c_void_p(foreground_before))
        outcome["cleanup"] = {"fixture_exit_code": None if fixture is None else fixture.poll(),
            "foreground_before": foreground_before,
            "foreground_before_restore": before_restore,
            "foreground_after_restore": int(user32.GetForegroundWindow() or 0),
            "appserver_closed": outcome.get("appserver_closed")}
        if outcome.get("status") == "PASS" and not (
                outcome["cleanup"]["fixture_exit_code"] == 0 and
                outcome["cleanup"]["foreground_before"] == outcome["cleanup"]["foreground_after_restore"] and
                outcome.get("appserver_closed") is True):
            outcome["status"] = "FAIL_OR_UNKNOWN"
        outcome["finished_monotonic_ns"] = time.monotonic_ns()
        save(cell_root / "result.json", outcome)
        (cell_root / "SHA256SUMS").write_text("".join(
            f"{sha(p.read_bytes())}  {p.relative_to(cell_root).as_posix()}\n"
            for p in sorted(cell_root.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"),
            encoding="utf-8", newline="\n")
    return outcome


async def run():
    if RUN.exists():
        raise FileExistsError("R12 run folder exists; do not replay this study")
    (RUN / "cells").mkdir(parents=True)
    cells = [
        {"index": 0, "cell_id": "pair1-direct", "pair": 1, "arm": "direct"},
        {"index": 1, "cell_id": "pair1-compiled", "pair": 1, "arm": "compiled"},
        {"index": 2, "cell_id": "pair2-compiled", "pair": 2, "arm": "compiled"},
        {"index": 3, "cell_id": "pair2-direct", "pair": 2, "arm": "direct"},
    ]
    results = []
    for spec in cells:
        result = await run_cell(spec)
        results.append(result)
        cleanup = result.get("cleanup") or {}
        if cleanup.get("fixture_exit_code") != 0 or cleanup.get("foreground_before") != cleanup.get("foreground_after_restore"):
            break
    by_id = {row["cell_id"]: row for row in results}
    paired = []
    for pair, direct_id, compiled_id in ((1, "pair1-direct", "pair1-compiled"),
                                         (2, "pair2-direct", "pair2-compiled")):
        direct, compiled = by_id.get(direct_id), by_id.get(compiled_id)
        if direct and compiled:
            metrics = ("elapsed_ns", "appserver_latency_ns", "provider_turn_count")
            delta = {metric: (direct.get(metric) - compiled.get(metric))
                if type(direct.get(metric)) is int and type(compiled.get(metric)) is int else None
                for metric in metrics}
            delta["input_tokens"] = ((direct.get("reported_tokens") or {}).get("input_tokens", 0)
                - (compiled.get("reported_tokens") or {}).get("input_tokens", 0))
            delta["output_tokens"] = ((direct.get("reported_tokens") or {}).get("output_tokens", 0)
                - (compiled.get("reported_tokens") or {}).get("output_tokens", 0))
            delta["observation_calls"] = ((direct.get("public_call_counts") or {}).get("observation", 0)
                - (compiled.get("public_call_counts") or {}).get("observation", 0))
            delta["dispatch_calls"] = ((direct.get("public_call_counts") or {}).get("dispatch", 0)
                - (compiled.get("public_call_counts") or {}).get("dispatch", 0))
            paired.append({"pair": pair, "direct_cell": direct_id,
                "compiled_cell": compiled_id, "direct_minus_compiled": delta,
                "both_task_pass": direct.get("status") == compiled.get("status") == "PASS"})
    summary = {"study_id": CONDITIONS["study_id"],
        "classification": "PASS_SCOPED_COUNTERBALANCED_WIN32_MATCHED_STUDY" if len(results) == 4 and all(r.get("status") == "PASS" for r in results) else "FAIL_OR_INCOMPLETE_FIRST_OUTCOME_RETAINED",
        "source_commit": CONDITIONS["source_commit"], "conditions_sha256": sha((PACKET / "CONDITIONS.json").read_bytes()),
        "pretrial_sha256": sha((PACKET / "PRETRIAL_SHA256SUMS").read_bytes()),
        "python_version": sys.version, "cell_count": len(results),
        "cells": [{"cell_id": row["cell_id"], "pair": row["pair"], "arm": row["arm"],
            "status": row.get("status"), "elapsed_ns": row.get("elapsed_ns"),
            "appserver_latency_ns": row.get("appserver_latency_ns"),
            "provider_turn_count": row.get("provider_turn_count"),
            "reported_tokens": row.get("reported_tokens"),
            "public_call_counts": row.get("public_call_counts"),
            "error": row.get("error")} for row in results],
        "paired_differences": paired,
        "interpretation": CONDITIONS["interpretation"],
        "wslc_used": False, "docker_used": False}
    save(RUN / "summary.json", summary)
    (RUN / "SHA256SUMS").write_text("".join(
        f"{sha(p.read_bytes())}  {p.relative_to(RUN).as_posix()}\n"
        for p in sorted(RUN.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"),
        encoding="utf-8", newline="\n")
    print(json.dumps(summary, sort_keys=True, indent=2))


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(run(), timeout=600))


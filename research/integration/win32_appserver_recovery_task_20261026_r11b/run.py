"""One recovery-then-fresh-generation compiled Win32 task sample."""
import asyncio
import base64
import ctypes
import hashlib
import json
import multiprocessing
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from ctypes import wintypes

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
TARGET = "r11b-owned-fixture"
VK_SHIFT = 0x10

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "live_control"))
sys.path.insert(0, str(ROOT / "research" / "integration" / "standard_mcp_task_ledger_57_v1"))
from runtime.backends.win32_v1.backend import Win32Backend, virtual_key
from runtime.backends.win32_v1.backend import BUTTON_FLAGS
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.supervised_win32_compiled import run_public_compiled
from runtime.core_v1.compiled_gui import validate as validate_interface
from runtime.cli_v1.win32_supervisor_helpers import create_native_win32_components
from app_server_provider_to_public_mcp_v1 import (
    AppServerPublicMcpModelCall, parse_app_server_tool_request)
from recorded_integrated_efficiency_model_call_v1 import build_model_provider_call
from codex_app_server_client_v2 import CodexAppServerClient
from persistent_planner_adapter_v2 import PersistentPlannerAdapter


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2,
        ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def public_body(reply):
    texts = [c.text for c in reply.content if c.type == "text"]
    if len(texts) != 1:
        raise RuntimeError("public MCP reply did not contain exactly one JSON text row")
    return json.loads(texts[0])


def raw_report(body):
    receipt = body.get("receipt")
    source = receipt.get("source") if isinstance(receipt, dict) else None
    report = source.get("raw_report") if isinstance(source, dict) else None
    return report if isinstance(report, dict) else body


def compiled_interface():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "win32-r11b-appserver-recovered-fresh-generation-task",
        "session_scope": "one-fresh-owned-fixture-process",
        "surface": "fixture-window-client",
        "predicates": ["ready", "saved"],
        "symbols": {"fixture": {"kind": "target_reference",
            "target_reference": TARGET, "identity_predicate": "ready",
            "dependencies": ["ready"]}},
        "actions": {"save": {"target_symbol": "fixture",
            "operation": "click-type-save", "expected_effect": {"saved": True}}},
        "method": {"name": "one-grounded-click-and-save", "version": "1",
            "initial_state": "before", "max_transitions": 1,
            "max_runtime_ms": 10000,
            "states": {
                "before": {"branches": [{"when": {"ready": True, "saved": False},
                    "outcome": "action", "action": "save", "next_state": "after", "reason": None}]},
                "after": {"branches": [{"when": {"saved": True},
                    "outcome": "complete", "action": None, "next_state": None, "reason": None}]}}},
    }


def strict_schema(value):
    if type(value) is dict:
        return {"type": "object", "properties": {key: strict_schema(item)
            for key, item in value.items()}, "required": list(value),
            "additionalProperties": False}
    if type(value) is int:
        return {"type": "integer"}
    raise TypeError("unsupported strict-schema example")


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


def mcp_reply(body):
    return SimpleNamespace(content=[SimpleNamespace(text=json.dumps(body, allow_nan=False))])


def blocked_child(gate, entered, targets, action):
    if not gate.wait(10):
        return
    from runtime.backends.win32_v1.backend import Win32Backend, VK_SHIFT
    from runtime.backends.win32_v1.session import Win32RuntimeSession
    backend = Win32Backend(targets)
    original = backend.user32.SendInput

    def block_shift_keyup(count, inputs, size):
        item = inputs[0]
        if item.type == 1 and item.ki.wVk == VK_SHIFT and item.ki.dwFlags & 0x0002:
            entered.set()
            while True:
                time.sleep(0.05)
        return original(count, inputs, size)

    backend.user32.SendInput = block_shift_keyup
    program = action["program"]
    source = program["source"]
    Win32RuntimeSession(backend).dispatch(program,
        current_observation_seq=source["observation_seq"],
        current_binding_revision=source["binding_revision"])


class BlockedProducerFactory:
    def __init__(self, targets):
        self.targets = dict(targets)
        self.ctx = multiprocessing.get_context("spawn")
        self.entered = self.ctx.Event()
        self.process = None
        self.gate = None

    def __call__(self, action):
        self.entered.clear()
        self.gate = self.ctx.Event()
        self.process = self.ctx.Process(target=blocked_child,
            args=(self.gate, self.entered, self.targets, action), daemon=True)
        from runtime.guarded_win32_v1.win32_process_identity import Win32ProcessIdentityReader
        identity = Win32ProcessIdentityReader()
        return self.process, lambda: identity(self.process), self.gate.set

    def read_result(self, _process):
        raise RuntimeError("held producer unexpectedly returned without a result packet")


def key_state(targets):
    backend = Win32Backend(targets)
    try:
        generation = backend.target_generation(TARGET)
        down = backend._key_down_state(virtual_key("SHIFT"), TARGET)
        witness = backend._last_state_query_witness
        return {"target_generation": generation, "shift_down": down,
                "state_query_witness": witness, "observed_monotonic_ns": time.monotonic_ns()}
    finally:
        backend.close()


def input_state(targets):
    backend = Win32Backend(targets)
    try:
        witnesses = {}
        values = {}
        for name, vk in (("SHIFT", virtual_key("SHIFT")),
                         ("CTRL", virtual_key("CTRL")),
                         ("S", virtual_key("S")),
                         ("left_button", BUTTON_FLAGS["left"][2])):
            values[name] = backend._key_down_state(vk, TARGET)
            witnesses[name] = list(backend._last_state_query_witness)
        return {"target_generation": backend.target_generation(TARGET),
            "states": values, "state_query_witnesses": witnesses}
    finally:
        backend.close()


async def run():
    if RUN.exists():
        raise FileExistsError(f"immutable output path already exists: {RUN}")
    RUN.mkdir(parents=True)
    (RUN / "fixture").mkdir()
    (RUN / "server").mkdir()
    meta_path = RUN / "fixture" / "meta.json"
    effect_path = RUN / "fixture" / "effect.json"
    events_path = RUN / "fixture" / "events.jsonl"
    fixture_cmd = [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
        "--meta", str(meta_path), "--effect", str(effect_path), "--events", str(events_path)]
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    for function in (user32.IsWindow, user32.IsWindowVisible, user32.IsWindowEnabled):
        function.argtypes = [wintypes.HWND]
        function.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    original_foreground = int(user32.GetForegroundWindow() or 0)
    fixture = None
    server = None
    appserver = None
    planner = None
    factory_box = {}
    outcome = {"attempt_id": "win32-appserver-recovery-r11b-20261026",
        "classification": "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED",
        "source_commit": "6d769848fd576332a2939c618347076a72c00d27",
        "python_version": sys.version,
        "wslc_used": False, "docker_used": False}
    started = time.monotonic_ns()
    try:
        fixture = subprocess.Popen(fixture_cmd, cwd=ROOT,
            stdout=(RUN / "fixture" / "stdout.bin").open("wb"),
            stderr=(RUN / "fixture" / "stderr.bin").open("wb"))
        deadline = time.monotonic() + 10
        while not meta_path.exists() and fixture.poll() is None and time.monotonic() < deadline:
            await asyncio.sleep(.05)
        if fixture.poll() is not None or not meta_path.exists():
            raise RuntimeError("owned fixture did not become ready")
        hwnd = json.loads(meta_path.read_text(encoding="utf-8"))["hwnd"]
        if type(hwnd) is not int or hwnd <= 0 or not user32.IsWindow(ctypes.c_void_p(hwnd)):
            raise RuntimeError("fresh fixture HWND failed native validation")
        targets = {TARGET: hwnd}
        preflight = key_state(targets)
        window = {"hwnd": hwnd, "fixture_pid": fixture.pid,
            "is_window": bool(user32.IsWindow(ctypes.c_void_p(hwnd))),
            "visible": bool(user32.IsWindowVisible(ctypes.c_void_p(hwnd))),
            "enabled": bool(user32.IsWindowEnabled(ctypes.c_void_p(hwnd))),
            "foreground_hwnd": int(user32.GetForegroundWindow() or 0),
            "observed_monotonic_ns": time.monotonic_ns()}
        if (preflight["shift_down"] is not False or
                preflight["target_generation"] is None or
                window["foreground_hwnd"] != hwnd or not window["visible"] or not window["enabled"]):
            raise RuntimeError("fresh owned fixture/foreground/SHIFT-up preflight failed; no input sent")
        outcome.update({"fixture_command": fixture_cmd, "fixture_pid": fixture.pid,
            "target_hwnd": hwnd, "preflight": preflight, "window_preflight": window})

        owner_factory = lambda configured, root, _display: create_native_win32_components(configured, root)[0]
        def producer_factory(configured, _root, _display):
            factory = BlockedProducerFactory(configured)
            factory_box["factory"] = factory
            return factory
        server = create_server(targets, RUN / "server", display_name="Agent Interface Win32 Fixture",
            session_mode="supervised-win32", _supervised_win32_owner_factory=owner_factory,
            _supervised_win32_producer_factory=producer_factory)

        observe = public_body(await server.call_tool("interface_observe", {
            "target": TARGET, "frame": "window_client", "region": [0, 0, 400, 180]}))
        outcome["public_observation"] = observe
        observed_report = raw_report(observe)
        outcome["public_observation_raw_report"] = observed_report
        if observed_report.get("target_generation") != preflight["target_generation"]:
            raise RuntimeError("public observation generation did not match native preflight")
        program = {"schema": "agent-interface/program-v1", "program_id": "r11b-held-shift-recovery",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {TARGET: preflight["target_generation"]}},
            "authority": {"lease_id": "r11b-one-shot", "expires_at_ns": time.monotonic_ns() + 15_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": TARGET},
                {"op": "key_state", "key": "SHIFT", "down": True},
                {"op": "key_state", "key": "SHIFT", "down": False},
                {"op": "release_all"}]}
        action_task = asyncio.create_task(server.call_tool("interface_dispatch", {
            "program": program, "current_observation_seq": 1,
            "current_binding_revision": 1, "wait_for_result_ms": 10000}))
        factory = None
        end = time.monotonic() + 10
        while time.monotonic() < end:
            factory = factory_box.get("factory")
            if factory and factory.entered.wait(.05):
                break
            await asyncio.sleep(.05)
        if not factory or not factory.entered.is_set():
            raise RuntimeError("producer did not enter the frozen blocked-call boundary")
        outcome["block_entered_monotonic_ns"] = time.monotonic_ns()
        outcome["state_during_hold"] = key_state(targets)
        if outcome["state_during_hold"]["shift_down"] is not True:
            raise RuntimeError("real SHIFT-down was not independently observed while producer held")
        call_id = None
        for _ in range(100):
            for request in (RUN / "server").glob("*/request.json"):
                try:
                    row = json.loads(request.read_text(encoding="utf-8"))
                    if row.get("arguments", {}).get("program", {}).get("program_id") == program["program_id"]:
                        call_id = request.parent.name
                        break
                except (OSError, ValueError):
                    pass
            if call_id:
                break
            await asyncio.sleep(.02)
        if not call_id:
            raise RuntimeError("unique public dispatch call ID was not retained")
        outcome["call_id"] = call_id
        cancel_started = time.monotonic_ns()
        cancel = public_body(await server.call_tool("interface_cancel", {"call_id": call_id}))
        cancel_returned = time.monotonic_ns()
        outcome["cancel"] = cancel
        outcome["cancel_started_monotonic_ns"] = cancel_started
        outcome["cancel_returned_monotonic_ns"] = cancel_returned
        outcome["cancel_latency_ns"] = cancel_returned - cancel_started
        if action_task.done():
            outcome["dispatch_terminal"] = public_body(await action_task)
        else:
            outcome["dispatch_terminal"] = public_body(await asyncio.wait_for(action_task, 6))
        outcome["state_after_recovery"] = key_state(targets)
        retained = public_body(await server.call_tool("interface_results", {"call_id": call_id}))
        outcome["retained_result"] = retained
        cancellation = retained.get("cancellation") or {}
        custody = cancellation.get("result") or {}
        outcome["cleanup_timing"] = {key: custody.get(key) for key in (
            "cleanup_requested_monotonic_ns", "recovery_completed_monotonic_ns",
            "cleanup_latency_ns", "cleanup_deadline_ns", "cleanup_latency_perf_counter_ns",
            "cleanup_deadline_perf_counter_ns")}
        outcome["effect_file_present"] = effect_path.exists()
        outcome["fixture_events"] = [json.loads(row) for row in events_path.read_text(encoding="utf-8").splitlines()]
        no_task_effect_events = all(event.get("kind") == "ready" for event in outcome["fixture_events"])
        outcome["fixture_has_no_task_effect_events"] = no_task_effect_events
        outcome["effect_file"] = (effect_path.read_bytes().decode("utf-8") if effect_path.exists() else None)
        released = outcome["state_after_recovery"]["shift_down"] is False
        recovered = cancellation.get("status") == "recovered" and cancellation.get("release_confirmed") is True
        latency = outcome["cleanup_timing"].get("cleanup_latency_ns")
        outcome["classification"] = ("PASS_SCOPED_BOUNDED_RECOVERY" if
            recovered and released and type(latency) is int and latency < 3_000_000_000
            and not outcome["effect_file_present"] and no_task_effect_events and
            outcome["state_after_recovery"]["target_generation"] == preflight["target_generation"]
            else "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED")
        outcome["recovery_phase"] = {
            "classification": outcome["classification"],
            "old_target_generation": preflight["target_generation"],
            "old_fixture_pid": fixture.pid,
            "old_call_id": call_id,
            "release_confirmed": cancellation.get("release_confirmed"),
            "same_generation_readback_up": released,
            "cleanup_latency_ns": latency,
            "cleanup_deadline_ns": outcome["cleanup_timing"].get("cleanup_deadline_ns"),
        }
        if outcome["classification"] != "PASS_SCOPED_BOUNDED_RECOVERY":
            raise RuntimeError("recovery phase did not pass its frozen gate; no continuation task attempted")

        # End the recovery session and destroy its target before admitting any
        # continuation task. A fresh fixture and server receive a new generation.
        outcome["recovery_session_close"] = public_body(await server.call_tool("interface_close", {}))
        server = None
        old_fixture_pid = fixture.pid
        old_generation = preflight["target_generation"]
        old_meta_path = meta_path
        if fixture.poll() is None:
            user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0010, 0, 0)
            fixture.wait(timeout=5)
        outcome["recovery_fixture_exit_code"] = fixture.poll()
        fixture = None

        # New process, HWND, call registry, native supervisor and task oracle.
        task_fixture_dir = RUN / "task-fixture"
        task_fixture_dir.mkdir()
        task_server_dir = RUN / "task-server"
        task_server_dir.mkdir()
        meta_path = task_fixture_dir / "meta.json"
        effect_path = task_fixture_dir / "effect.json"
        events_path = task_fixture_dir / "events.jsonl"
        fixture_cmd = [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
            "--meta", str(meta_path), "--effect", str(effect_path), "--events", str(events_path)]
        fixture = subprocess.Popen(fixture_cmd, cwd=ROOT,
            stdout=(task_fixture_dir / "stdout.bin").open("wb"),
            stderr=(task_fixture_dir / "stderr.bin").open("wb"))
        deadline = time.monotonic() + 10
        while not meta_path.exists() and fixture.poll() is None and time.monotonic() < deadline:
            await asyncio.sleep(.05)
        if fixture.poll() is not None or not meta_path.exists():
            raise RuntimeError("fresh continuation fixture did not become ready")
        task_hwnd = json.loads(meta_path.read_text(encoding="utf-8"))["hwnd"]
        task_targets = {TARGET: task_hwnd}
        task_generation_native = key_state(task_targets)
        task_window = {"hwnd": task_hwnd, "fixture_pid": fixture.pid,
            "is_window": bool(user32.IsWindow(ctypes.c_void_p(task_hwnd))),
            "visible": bool(user32.IsWindowVisible(ctypes.c_void_p(task_hwnd))),
            "enabled": bool(user32.IsWindowEnabled(ctypes.c_void_p(task_hwnd))),
            "foreground_hwnd": int(user32.GetForegroundWindow() or 0),
            "observed_monotonic_ns": time.monotonic_ns()}
        outcome["fresh_task_preflight"] = {"fixture_pid": fixture.pid,
            "previous_fixture_pid": old_fixture_pid, "window": task_window,
            "native_identity": task_generation_native}
        if (fixture.pid == old_fixture_pid or task_generation_native["shift_down"] is not False
                or task_generation_native["target_generation"] == old_generation
                or task_window["foreground_hwnd"] != task_hwnd
                or not task_window["is_window"] or not task_window["visible"]
                or not task_window["enabled"]):
            raise RuntimeError("fresh process/generation/foreground preflight failed; no continuation input sent")
        oracle_calls = []
        expected_effect = {"saved": True, "text": "office", "clicked": True}
        def task_oracle(action):
            oracle_calls.append(dict(action))
            if effect_path.is_file():
                raw_effect = effect_path.read_bytes()
                try:
                    effect = json.loads(raw_effect)
                except (ValueError, UnicodeDecodeError):
                    effect = None
            else:
                raw_effect = b"missing-effect-file"
                effect = None
            return {"call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "321a2f10e7784cb3aa71f8d1b5f0721e",
                "outcome": "success" if effect == expected_effect else "failure",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-effect:sha256:" + sha(raw_effect)}

        server = create_server(task_targets, task_server_dir,
            display_name="Agent Interface Win32 Fixture R11 Task",
            session_mode="supervised-win32", supervised_win32_task_oracle=task_oracle)
        stale_program = {"schema": "agent-interface/program-v1",
            "program_id": "r11b-old-generation-focus-probe",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {TARGET: old_generation}},
            "authority": {"lease_id": "r11b-stale-probe",
                "expires_at_ns": time.monotonic_ns() + 10_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": TARGET}, {"op": "release_all"}]}
        stale_body = public_body(await server.call_tool("interface_dispatch", {
            "program": stale_program, "current_observation_seq": 1,
            "current_binding_revision": 1, "wait_for_result_ms": 10000}))
        stale_raw = raw_report(stale_body)
        outcome["stale_generation_probe"] = {"body": stale_body, "raw_report": stale_raw,
            "input_dispatched": stale_raw.get("input_dispatched", stale_body.get("input_dispatched")),
            "refusal_reason": stale_raw.get("error", stale_body.get("error")),
            "effect_file_present": effect_path.exists()}
        if (outcome["stale_generation_probe"]["input_dispatched"] is not False
                or outcome["stale_generation_probe"]["refusal_reason"] != "TARGET_GENERATION_CHANGED"
                or effect_path.exists()):
            raise RuntimeError("old-generation probe was not refused before input/effect")

        initial_observation = await server.call_tool("interface_observe", {
            "target": TARGET, "frame": "window_client", "region": [0, 0, 400, 180]})
        initial_body = public_body(initial_observation)
        initial_raw = raw_report(initial_body)
        outcome["fresh_task_public_observation"] = {"body": initial_body,
            "raw_report": initial_raw}
        if initial_raw.get("target_generation") != task_generation_native["target_generation"]:
            raise RuntimeError("fresh public observation generation differs from native preflight")

        images = [item for item in initial_observation.content
            if getattr(item, "type", None) == "image"]
        if len(images) != 1:
            raise RuntimeError("model grounding requires exactly one fresh public observation image")
        image_data = getattr(images[0], "data", None)
        if not isinstance(image_data, str):
            raise RuntimeError("fresh observation image lacks base64 data")
        model_dir = RUN / "app-server"
        model_dir.mkdir()
        model_workspace = RUN / "empty-workspace"
        model_workspace.mkdir()
        protocol_journal = model_dir / "protocol.jsonl"
        image_path = RUN / "model-grounding.png"
        image_path.write_bytes(base64.b64decode(image_data, validate=True))
        from PIL import Image
        with Image.open(image_path) as image:
            image_dimensions = list(image.size)
        if image_dimensions != [400, 180]:
            raise RuntimeError("fresh model grounding image dimensions differ from the frozen fixture region")
        model_command = appserver_command()
        save(model_dir / "invocation.json", {"command": model_command,
            "cwd": str(model_workspace), "model": "gpt-6.1-sol", "effort": "low",
            "sandbox": "read-only", "wslc_used": False, "docker_used": False})
        appserver = CodexAppServerClient(model_command, cwd=model_workspace,
            journal_path=protocol_journal)
        save(model_dir / "initialize.json", appserver.initialize(
            name="agent-interface-r11", version="1"))
        planner = PersistentPlannerAdapter(appserver, model="gpt-6.1-sol", effort="low",
            cwd=str(model_workspace), base_instructions=(
                "Return only the JSON object requested by the user and match the supplied schema. "
                "Do not invoke tools or add explanation."))
        thread_id = planner.start_session()
        save(model_dir / "thread-started.json", {"thread_id": thread_id})
        model_call = AppServerPublicMcpModelCall(planner, protocol_journal,
            workspace=model_workspace, contract="win32-grounded-coordinate-r11",
            output_schema=strict_schema({"x": 100, "y": 60}), model="gpt-6.1-sol",
            effort="low", path_converter=str, turn_timeout=90)
        prompt = ("From the supplied screenshot of the owned fixture window, choose one point "
            "inside the fixture client area, within x=24..300 and y=24..150, that safely marks "
            "the fixture as clicked. Return only integer x and y. The caller will type the fixed "
            "harmless word office and save only inside the disposable fixture process. "
            "Image coordinate origin is the top-left of this 400x180 window-client screenshot.")
        request_bytes, provider_call = build_model_provider_call(model_call=model_call.call,
            root=RUN / "provider-call", prompt=prompt, image=image_path,
            contract="win32-grounded-coordinate-r11", workspace=model_workspace)
        (model_dir / "provider-request.bin").write_bytes(request_bytes)
        model_started = time.monotonic_ns()
        generation_record = await provider_call()
        model_returned = time.monotonic_ns()
        save(model_dir / "provider-terminal.json", {key: value for key, value
            in generation_record.items() if key not in {"response_bytes", "backend_result"}})
        if generation_record.get("status") != "completed":
            raise RuntimeError("AppServer grounding turn did not complete; no task input attempted")
        backend_result = generation_record.get("backend_result") or {}
        answer = parse_app_server_tool_request(generation_record["response_bytes"],
            thread_id=backend_result["thread_id"], turn_id=backend_result["turn_id"])
        bounds = {"x": [24, 300], "y": [24, 150]}
        if (type(answer.get("x")) is not int or type(answer.get("y")) is not int
                or not bounds["x"][0] <= answer["x"] <= bounds["x"][1]
                or not bounds["y"][0] <= answer["y"] <= bounds["y"][1]):
            raise RuntimeError("AppServer coordinate is outside preregistered fixture bounds; no input attempted")
        (model_dir / "provider-response.jsonl").write_bytes(generation_record["response_bytes"])
        outcome["model_decision"] = {"answer": answer, "bounds": bounds,
            "action_coordinate": {"x": answer["x"], "y": answer["y"]},
            "model": "gpt-6.1-sol", "effort": "low", "status": generation_record["status"],
            "usage": generation_record.get("usage"), "backend_usage": backend_result.get("usage"),
            "usage_matches_backend_journal": (generation_record.get("usage", {}).get("status") == "reported" and all(generation_record.get("usage", {}).get(key) == value for key, value in (backend_result.get("usage") or {}).items())),
            "grounding_generation": initial_raw.get("target_generation"),
            "observation_capture_started_ns": (initial_raw.get("observation") or {}).get("capture_started_ns"),
            "model_started_monotonic_ns": model_started,
            "model_returned_monotonic_ns": model_returned,
            "model_latency_ns": model_returned - model_started,
            "image_sha256": sha(image_path.read_bytes()), "image_dimensions": image_dimensions}
        save(model_dir / "decision.json", outcome["model_decision"])

        interface = compiled_interface()
        validate_interface(interface)
        action_return = {"monotonic_ns": None}
        task_action = {"call_id": None, "raw_report": None, "body": None}
        loop = asyncio.get_running_loop()
        compiled_observations = []

        def observe_callback(target, frame, region):
            future = asyncio.run_coroutine_threadsafe(server.call_tool("interface_observe", {
                "target": target, "frame": frame, "region": region}), loop)
            reply = future.result(timeout=20)
            observed_body = public_body(reply)
            observed_report = raw_report(observed_body)
            compiled_observations.append({"target_generation": observed_report.get("target_generation"),
                "capture_started_ns": (observed_report.get("observation") or {}).get("capture_started_ns"),
                "sequence": (observed_report.get("observation") or {}).get("sequence")})
            return reply

        def dispatch_callback(program_to_send, sequence, binding_revision):
            outcome["submitted_task_program"] = program_to_send
            future = asyncio.run_coroutine_threadsafe(server.call_tool("interface_dispatch", {
                "program": program_to_send, "current_observation_seq": sequence,
                "current_binding_revision": binding_revision,
                "wait_for_result_ms": 10000}), loop)
            reply = future.result(timeout=20)
            action_return["monotonic_ns"] = time.monotonic_ns()
            body = public_body(reply)
            report = raw_report(body)
            task_action.update(call_id=body.get("call_id"), raw_report=report, body=body)
            save(RUN / "compiled-dispatch.json", {"body": body, "raw_report": report,
                "response_returned_monotonic_ns": action_return["monotonic_ns"]})
            return reply

        def perceive(_report, _reply):
            saved = False
            if effect_path.is_file():
                try:
                    saved = json.loads(effect_path.read_text(encoding="utf-8")) == expected_effect
                except (OSError, ValueError):
                    saved = False
            return {"ready": True, "saved": saved}

        def verify_effect(request, post_report, _reply):
            observation = post_report.get("observation") or {}
            capture_started = observation.get("capture_started_ns")
            exact = False
            effect_digest = None
            if effect_path.is_file():
                raw_effect = effect_path.read_bytes()
                effect_digest = sha(raw_effect)
                try:
                    exact = json.loads(raw_effect) == expected_effect
                except (ValueError, UnicodeDecodeError):
                    exact = False
            fresh = (type(capture_started) is int and type(action_return["monotonic_ns"]) is int
                and capture_started >= action_return["monotonic_ns"])
            audit = {"status": "succeeded" if exact and fresh else "failed",
                "effect_sha256": effect_digest,
                "post_observation_capture_started_ns": capture_started,
                "dispatch_response_returned_ns": action_return["monotonic_ns"],
                "post_observation_fresh_after_dispatch_return": fresh}
            save(RUN / "effect-verification-audit.json", audit)
            return {"status": audit["status"],
                "evidence_ref": effect_digest if exact and effect_digest else "effect-missing-or-mismatch"}

        task_program = {"schema": "agent-interface/program-v1",
            "program_id": "r11b-appserver-grounded-click-save",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {TARGET: task_generation_native["target_generation"]}},
            "authority": {"lease_id": "r11b-task-lease",
                "expires_at_ns": time.monotonic_ns() + 20_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": TARGET},
                {"op": "pointer_move", "frame": "window_client", "x": answer["x"], "y": answer["y"]},
                {"op": "pointer_button", "button": "left", "down": True},
                {"op": "pointer_button", "button": "left", "down": False},
                {"op": "wait_update", "timeout_ms": 100},
                {"op": "text", "text": "office"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"}]}
        outcome["task_program"] = task_program
        from runtime.core_v1.contract import validate_program
        validate_program(task_program)
        compiled_receipt = await asyncio.to_thread(run_public_compiled,
            interface, {"save": task_program}, target=TARGET,
            current_binding_revision=1, region=[0, 0, 400, 180],
            observe=observe_callback, dispatch=dispatch_callback,
            perceive=perceive, verify_effect=verify_effect,
            expected_generation=task_generation_native["target_generation"],
            cancelled=lambda: False)
        save(RUN / "compiled-task-receipt.json", compiled_receipt)
        outcome["compiled_task_receipt"] = compiled_receipt
        action_ids = compiled_receipt.get("standard_action_call_ids")
        if type(action_ids) is not list or len(action_ids) != 1 or task_action["call_id"] != action_ids[0]:
            raise RuntimeError("compiled caller did not preserve exactly one matching standard action call")
        outcome["task_action_call_id"] = action_ids[0]
        outcome["task_action_terminal"] = task_action
        retained_task = public_body(await server.call_tool("interface_results", {"call_id": action_ids[0]}))
        outcome["task_retained_result"] = retained_task
        action_record = retained_task.get("action") or {}
        action_result = action_record.get("result") or {}
        outcome["task_action_release_confirmed"] = action_record.get("release_confirmed")

        oracle_body = public_body(await server.call_tool("interface_verify_task", {
            "call_id": action_ids[0], "wait_for_result_ms": 3000}))
        outcome["task_oracle"] = oracle_body
        oracle_receipt = ((oracle_body.get("task_effect") or {}).get("receipt") or {})
        outcome["independent_effect"] = json.loads(effect_path.read_text(encoding="utf-8")) if effect_path.is_file() else None
        native_input_state = input_state(task_targets)
        neutral_state = {"target_generation": native_input_state["target_generation"],
            **native_input_state["states"],
            "state_query_witnesses": native_input_state["state_query_witnesses"]}
        outcome["task_neutral_readback"] = neutral_state
        task_events = [json.loads(row) for row in events_path.read_text(encoding="utf-8").splitlines()]
        outcome["task_fixture_events"] = task_events
        expected_call_id = action_ids[0]
        expected_operation_id = action_record.get("operation_id")
        effect_verified = (oracle_body.get("status") == "verified"
            and oracle_body.get("task_success") is True
            and oracle_receipt.get("call_id") == expected_call_id
            and oracle_receipt.get("operation_id") == expected_operation_id
            and oracle_receipt.get("target_generation") == task_generation_native["target_generation"]
            and oracle_receipt.get("oracle_id") == "321a2f10e7784cb3aa71f8d1b5f0721e")
        clean_input = (outcome["task_action_release_confirmed"] is True
            and neutral_state["target_generation"] == task_generation_native["target_generation"]
            and all(neutral_state[key] is False for key in ("SHIFT", "CTRL", "S", "left_button")))
        fresh_effect = (outcome["independent_effect"] == expected_effect
            and all(event.get("kind") in {"ready", "click", "char", "save"} for event in task_events)
            and sum(event.get("kind") == "click" for event in task_events) == 1
            and [event.get("code") for event in task_events if event.get("kind") == "char"]
                == list(map(ord, "office"))
            and sum(event.get("kind") == "save" for event in task_events) == 1)
        effect_timing = json.loads((RUN / "effect-verification-audit.json").read_text(encoding="utf-8"))
        timing_ok = effect_timing.get("post_observation_fresh_after_dispatch_return") is True
        stale_refused = (outcome["stale_generation_probe"]["input_dispatched"] is False
            and outcome["stale_generation_probe"]["effect_file_present"] is False)
        outcome["task_phase_checks"] = {"new_pid": fixture.pid != old_fixture_pid,
            "new_generation": task_generation_native["target_generation"] != old_generation,
            "stale_generation_refused_without_input": stale_refused,
            "model_turn_completed": outcome.get("model_decision", {}).get("status") == "completed",
            "model_coordinate_in_frozen_bounds": (bounds["x"][0] <= answer["x"] <= bounds["x"][1]
                and bounds["y"][0] <= answer["y"] <= bounds["y"][1]),
            "provider_usage_matches_appserver_journal": (
                outcome.get("model_decision", {}).get("usage", {}).get("status") == "reported"
                and outcome.get("model_decision", {}).get("usage_matches_backend_journal") is True),
            "compiled_observation_after_model_uses_grounded_generation": (
                bool(compiled_observations)
                and compiled_observations[0].get("target_generation") == outcome["model_decision"]["grounding_generation"]
                and type(compiled_observations[0].get("capture_started_ns")) is int
                and compiled_observations[0]["capture_started_ns"] >= outcome["model_decision"]["model_returned_monotonic_ns"]),
            "compiled_one_action": len(action_ids) == 1,
            "neutral_release": clean_input, "post_dispatch_fresh_observation": timing_ok,
            "exact_fixture_effect_and_event_sequence": fresh_effect,
            "independent_task_oracle": effect_verified,
            "task_success_bound_to_exact_action_generation": effect_verified}
        outcome["compiled_observations"] = compiled_observations
        final_checks = outcome["task_phase_checks"]
        outcome["classification"] = ("PASS_RECOVERY_FRESH_GENERATION_TASK" if
            outcome["recovery_phase"]["classification"] == "PASS_SCOPED_BOUNDED_RECOVERY"
            and all(final_checks.values()) else "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED")
    except BaseException as exc:
        outcome["classification"] = "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED"
        outcome.update({"error_type": type(exc).__name__, "error": str(exc)[:1000]})
    finally:
        if server is not None:
            try:
                outcome["close"] = public_body(await server.call_tool("interface_close", {}))
            except BaseException as exc:
                outcome["close_error"] = repr(exc)
        if appserver is not None:
            try:
                appserver.close(timeout=5)
                outcome["appserver_closed"] = True
            except BaseException as exc:
                outcome["appserver_closed"] = False
                outcome["appserver_close_error"] = repr(exc)
        try:
            if fixture is not None and fixture.poll() is None:
                final_before_cleanup = key_state({TARGET: json.loads(
                    meta_path.read_text(encoding="utf-8"))["hwnd"]})
                outcome["state_before_fallback_cleanup"] = final_before_cleanup
                exact_targets = {TARGET: json.loads(meta_path.read_text(encoding="utf-8"))["hwnd"]}
                final_input_state = input_state(exact_targets)
                outcome["all_inputs_before_fallback_cleanup"] = final_input_state
                if any(value is True for value in final_input_state["states"].values()):
                    backend = Win32Backend(exact_targets)
                    try:
                        backend.held_keys.update({"SHIFT": virtual_key("SHIFT"),
                            "CTRL": virtual_key("CTRL"), "S": virtual_key("S")})
                        backend.held_key_targets.update({key: TARGET for key in backend.held_keys})
                        backend.held_buttons.add("left")
                        backend.held_button_targets["left"] = TARGET
                        outcome["emergency_release"] = backend.release_all()
                    finally:
                        backend.close()
                    outcome["state_after_emergency_release"] = input_state(exact_targets)
                    outcome["classification"] = "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED"
        except BaseException as exc:
            outcome["fallback_cleanup_error"] = repr(exc)
        if fixture is not None and fixture.poll() is None:
            try:
                hwnd_now = json.loads(meta_path.read_text(encoding="utf-8"))["hwnd"]
                user32.PostMessageW(ctypes.c_void_p(hwnd_now), 0x0010, 0, 0)
                fixture.wait(timeout=5)
            except BaseException:
                fixture.terminate()
                try:
                    fixture.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    fixture.kill()
                    fixture.wait(timeout=3)
        before_restore = int(user32.GetForegroundWindow() or 0)
        if original_foreground and user32.IsWindow(ctypes.c_void_p(original_foreground)):
            user32.SetForegroundWindow(ctypes.c_void_p(original_foreground))
        outcome["cleanup"] = {"fixture_exit_code": None if fixture is None else fixture.poll(),
            "foreground_before": original_foreground, "foreground_before_restore": before_restore,
            "foreground_after_restore": int(user32.GetForegroundWindow() or 0),
            "finished_monotonic_ns": time.monotonic_ns()}
        if isinstance(outcome.get("task_phase_checks"), dict):
            outcome["task_phase_checks"]["appserver_closed"] = outcome.get("appserver_closed") is True
            outcome["task_phase_checks"]["task_fixture_exited_cleanly"] = outcome["cleanup"]["fixture_exit_code"] == 0
            outcome["task_phase_checks"]["foreground_restored"] = (
                outcome["cleanup"]["foreground_before"] == outcome["cleanup"]["foreground_after_restore"])
            if outcome["classification"] == "PASS_RECOVERY_FRESH_GENERATION_TASK":
                outcome["classification"] = ("PASS_RECOVERY_FRESH_GENERATION_TASK"
                    if all(outcome["task_phase_checks"].values())
                    else "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED")
        outcome["elapsed_ns"] = time.monotonic_ns() - started
        save(RUN / "result.json", outcome)
        (RUN / "SHA256SUMS").write_text("".join(
            f"{sha(p.read_bytes())}  {p.relative_to(RUN).as_posix()}\n"
            for p in sorted(RUN.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"),
            encoding="utf-8", newline="\n")
    print(json.dumps(outcome, sort_keys=True, indent=2))


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(run(), timeout=240))


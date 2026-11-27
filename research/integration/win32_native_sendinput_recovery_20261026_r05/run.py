"""One frozen public-MCP Win32 blocked-SendInput-entry recovery sample."""
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
from ctypes import wintypes

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
TARGET = "r05-owned-fixture"
VK_SHIFT = 0x10

sys.path.insert(0, str(ROOT))
from runtime.backends.win32_v1.backend import Win32Backend, virtual_key
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.win32_supervisor_helpers import create_native_win32_components


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
    factory_box = {}
    outcome = {"attempt_id": "win32-native-sendinput-r05-20261026",
        "classification": "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED",
        "source_commit": "f2f7dbb2e043919e0773655e5fab543cc3682fcd",
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
        if observe.get("target_generation") != preflight["target_generation"]:
            raise RuntimeError("public observation generation did not match native preflight")
        program = {"schema": "agent-interface/program-v1", "program_id": "r05-held-shift-recovery",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {TARGET: preflight["target_generation"]}},
            "authority": {"lease_id": "r05-one-shot", "expires_at_ns": time.monotonic_ns() + 15_000_000_000},
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
        outcome["fixture_events"] = events_path.read_text(encoding="utf-8").splitlines()
        outcome["effect_file"] = (effect_path.read_bytes().decode("utf-8") if effect_path.exists() else None)
        released = outcome["state_after_recovery"]["shift_down"] is False
        recovered = cancellation.get("status") == "recovered" and cancellation.get("release_confirmed") is True
        latency = outcome["cleanup_timing"].get("cleanup_latency_ns")
        outcome["classification"] = ("PASS_SCOPED_BOUNDED_RECOVERY" if
            recovered and released and type(latency) is int and latency < 3_000_000_000
            and not outcome["effect_file_present"] and
            outcome["state_after_recovery"]["target_generation"] == preflight["target_generation"]
            else "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED")
    except BaseException as exc:
        outcome.update({"error_type": type(exc).__name__, "error": str(exc)[:1000]})
    finally:
        if server is not None:
            try:
                outcome["close"] = public_body(await server.call_tool("interface_close", {}))
            except BaseException as exc:
                outcome["close_error"] = repr(exc)
        try:
            if fixture is not None and fixture.poll() is None:
                final_before_cleanup = key_state({TARGET: json.loads(
                    meta_path.read_text(encoding="utf-8"))["hwnd"]})
                outcome["state_before_fallback_cleanup"] = final_before_cleanup
                if final_before_cleanup["shift_down"] is True:
                    backend = Win32Backend({TARGET: json.loads(
                        meta_path.read_text(encoding="utf-8"))["hwnd"]})
                    try:
                        backend.held_keys["SHIFT"] = VK_SHIFT
                        backend.held_key_targets["SHIFT"] = TARGET
                        outcome["emergency_release"] = backend.release_all()
                    finally:
                        backend.close()
                    outcome["state_after_emergency_release"] = key_state({TARGET: json.loads(
                        meta_path.read_text(encoding="utf-8"))["hwnd"]})
                    outcome["classification"] = "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED"
        except BaseException as exc:
            outcome["fallback_cleanup_error"] = repr(exc)
        if fixture is not None and fixture.poll() is None:
            try:
                hwnd_now = json.loads((RUN / "fixture" / "meta.json").read_text(encoding="utf-8"))["hwnd"]
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
        outcome["elapsed_ns"] = time.monotonic_ns() - started
        save(RUN / "result.json", outcome)
        (RUN / "SHA256SUMS").write_text("".join(
            f"{sha(p.read_bytes())}  {p.relative_to(RUN).as_posix()}\n"
            for p in sorted(RUN.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"),
            encoding="utf-8", newline="\n")
    print(json.dumps(outcome, sort_keys=True, indent=2))


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(run(), timeout=90))

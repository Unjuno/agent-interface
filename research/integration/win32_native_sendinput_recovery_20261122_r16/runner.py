"""One-shot public orphan recovery for the retained R14 Win32 custody fence."""
from __future__ import annotations

import asyncio
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
CONDITIONS = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
ATTEMPT = CONDITIONS["attempt_id"]
TARGET = CONDITIONS["recovery"]["target_name"]
SOURCE = CONDITIONS["source_evidence"]
SOURCE_RECORD = CONDITIONS["source_custody_record"]
FENCE = CONDITIONS["persistent_fence"]
sys.path.insert(0, str(ROOT))

from runtime.backends.win32_v1.backend import Win32Backend, virtual_key
from runtime.cli_v1.mcp_server import create_server


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2,
        ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def public_body(reply):
    rows = [item.text for item in reply.content if item.type == "text"]
    if len(rows) != 1:
        raise RuntimeError("public MCP reply did not contain exactly one JSON row")
    return json.loads(rows[0])


def raw_report(body):
    receipt = body.get("receipt")
    source = receipt.get("source") if isinstance(receipt, dict) else None
    report = source.get("raw_report") if isinstance(source, dict) else None
    return report if isinstance(report, dict) else body


def exact_producer_status(identity):
    """Read-only PID/creation-time check; never terminates a process."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x1000, False, identity["pid"])
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:
            return {"identity": identity, "observed_producer_live": False,
                    "basis": "OpenProcess ERROR_INVALID_PARAMETER: PID absent",
                    "observed_monotonic_ns": time.monotonic_ns()}
        raise OSError(error, "exact producer identity query failed")

    class FILETIME(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    creation, exited, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    try:
        if not kernel32.GetProcessTimes(handle, ctypes.byref(creation),
                ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)):
            raise OSError(ctypes.get_last_error(), "GetProcessTimes failed")
        observed = (int(creation.high) << 32) | int(creation.low)
    finally:
        kernel32.CloseHandle(handle)
    live = observed == identity["creation_time_100ns"]
    return {"identity": identity, "observed_creation_time_100ns": observed,
            "observed_producer_live": live,
            "basis": "PID creation-time equality" if live else "PID was reused by a different process",
            "observed_monotonic_ns": time.monotonic_ns()}


def read_fence(path: Path):
    raw = path.read_bytes()
    return raw, {"sha256": digest(raw), "state": json.loads(raw.decode("utf-8"))}


def write_manifest(root: Path, manifest_name: str) -> None:
    rows = []
    for path in sorted(item for item in root.rglob("*")
                       if item.is_file() and item.name != manifest_name):
        rows.append(f"{digest(path.read_bytes())}  {path.relative_to(root).as_posix()}")
    (root / manifest_name).write_text("\n".join(rows) + "\n",
        encoding="ascii", newline="\n")


def verify_pretrial_freeze() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
        text=True).strip()
    if head != CONDITIONS["source_main"]:
        raise RuntimeError(f"source HEAD changed after freeze: {head}")
    manifest = PACKET / "PRETRIAL_SHA256SUMS"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, relative = line.split("  ", 1)
        path = (ROOT / relative).resolve()
        path.relative_to(ROOT.resolve())
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise RuntimeError(f"frozen pretrial input mismatch: {relative}")


async def wait_for_activation(ready_path: Path, receipt_path: Path,
                              fixture: subprocess.Popen, hwnd: int):
    save(ready_path, {"attempt_id": ATTEMPT, "stage": "recovery-target",
        "hwnd": hwnd, "fixture_pid": fixture.pid, "timeout_seconds": 180})
    end = time.monotonic() + 180
    while time.monotonic() < end and not receipt_path.exists():
        if fixture.poll() is not None:
            raise RuntimeError("fixture exited before Computer Use activation")
        await asyncio.sleep(.05)
    if not receipt_path.exists():
        raise TimeoutError("Computer Use activation receipt missing; no public recovery submitted")
    row = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (row.get("attempt_id") != ATTEMPT or row.get("stage") != "recovery-target"
            or row.get("fixture_window_id") != hwnd
            or row.get("activate_call_returned") is not True
            or row.get("state_capture_returned") is not True):
        raise RuntimeError("activation receipt did not bind the exact fixture HWND")
    return row


async def run():
    if os.name != "nt":
        raise RuntimeError("R16 requires the authorized Windows workstation")
    verify_pretrial_freeze()
    if RUN.exists():
        raise FileExistsError(f"immutable output already exists: {RUN}")
    RUN.mkdir(parents=True)
    (RUN / "fixture").mkdir()
    (RUN / "server").mkdir()
    outcome = {"attempt_id": ATTEMPT, "source_main": CONDITIONS["source_main"],
        "started_monotonic_ns": time.monotonic_ns(), "task_dispatch_attempted": False,
        "public_recovery_attempt_count": 0}
    fixture = None
    server = None
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsWindowEnabled.argtypes = [wintypes.HWND]
    user32.IsWindowEnabled.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    original_foreground = int(user32.GetForegroundWindow() or 0)
    should_preserve_fixture = True
    try:
        fence_path = (Path(os.environ["LOCALAPPDATA"]) / "Unjuno" / "AgentInterface"
            / "custody-v1" / (FENCE["namespace_digest"] + ".json"))
        before_bytes, before = read_fence(fence_path)
        outcome["fence_before"] = before
        if (before["sha256"] != FENCE["expected_sha256_before"]
                or before["state"].get("status") != FENCE["expected_status"]
                or before["state"].get("revision") != FENCE["expected_revision"]
                or before["state"].get("pending", {}).get("operation_id") != SOURCE["operation_id"]
                or before["state"].get("pending", {}).get("target_generation") != SOURCE["target_generation"]
                or before["state"].get("pending", {}).get("obligations") != SOURCE["obligations"]):
            raise RuntimeError("durable source fence differs from frozen R14 evidence")
        outcome["source_process_identity_check"] = exact_producer_status(SOURCE["producer_identity"])
        if outcome["source_process_identity_check"]["observed_producer_live"] is not False:
            raise RuntimeError("exact R14 producer identity is still live; no recovery API call made")

        fixture_dir = RUN / "fixture"
        meta_path = fixture_dir / "meta.json"
        effect_path = fixture_dir / "effect.json"
        events_path = fixture_dir / "events.jsonl"
        fixture_cmd = [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
            "--meta", str(meta_path), "--effect", str(effect_path), "--events", str(events_path)]
        save(fixture_dir / "launch.json", {"argv": fixture_cmd, "cwd": str(ROOT),
            "created_monotonic_ns": time.monotonic_ns()})
        fixture = subprocess.Popen(fixture_cmd, cwd=ROOT,
            stdout=(fixture_dir / "stdout.bin").open("wb"),
            stderr=(fixture_dir / "stderr.bin").open("wb"))
        wait_end = time.monotonic() + 10
        while not meta_path.exists() and fixture.poll() is None and time.monotonic() < wait_end:
            await asyncio.sleep(.05)
        if fixture.poll() is not None or not meta_path.exists():
            raise RuntimeError("recovery fixture failed to become ready")
        hwnd = json.loads(meta_path.read_text(encoding="utf-8"))["hwnd"]
        outcome["fixture_pre_activation"] = {"pid": fixture.pid, "hwnd": hwnd,
            "is_window": bool(user32.IsWindow(hwnd)), "visible": bool(user32.IsWindowVisible(hwnd)),
            "enabled": bool(user32.IsWindowEnabled(hwnd)),
            "foreground_hwnd": int(user32.GetForegroundWindow() or 0),
            "observed_monotonic_ns": time.monotonic_ns()}
        if not all(outcome["fixture_pre_activation"][key] for key in ("is_window", "visible", "enabled")):
            raise RuntimeError("recovery fixture HWND preflight failed")
        outcome["computer_use_activation"] = await wait_for_activation(
            fixture_dir / "activation-ready.json", fixture_dir / "computer-use-activation.json",
            fixture, hwnd)
        targets = {TARGET: hwnd}
        backend = Win32Backend(targets)
        try:
            native_generation = backend.target_generation(TARGET)
            shift_down = backend._key_down_state(virtual_key("SHIFT"), TARGET)
            witness = list(backend._last_state_query_witness)
        finally:
            backend.close()
        outcome["native_recovery_target_preflight"] = {"target_generation": native_generation,
            "shift_down": shift_down, "state_query_witness": witness,
            "foreground_hwnd": int(user32.GetForegroundWindow() or 0),
            "observed_monotonic_ns": time.monotonic_ns()}
        if (native_generation == SOURCE["target_generation"] or shift_down is not False
                or outcome["native_recovery_target_preflight"]["foreground_hwnd"] != hwnd):
            raise RuntimeError("recovery target is not fresh, foreground, and neutral")

        server = create_server(targets, RUN / "server",
            display_name="Agent Interface Win32 R16 Orphan Recovery",
            session_mode="supervised-win32",
            supervised_win32_late_input_horizon_ns=2_000_000_000)
        observation = public_body(await server.call_tool("interface_observe", {
            "target": TARGET, "frame": "window_client", "region": [0, 0, 400, 180]}))
        observation_raw = raw_report(observation)
        outcome["public_recovery_observation"] = {"body": observation,
            "raw_report": observation_raw}
        observed_generation = observation_raw.get("target_generation")
        if observed_generation != native_generation:
            raise RuntimeError("public observed recovery generation differs from native preflight")
        outcome["recovery_generation"] = observed_generation

        outcome["public_recovery_attempt_count"] = 1
        recovery_body = public_body(await server.call_tool("interface_recover_orphaned_input", {
            "source_operation_id": SOURCE["operation_id"],
            "source_target_generation": SOURCE["target_generation"],
            "recovery_target_generation": observed_generation,
            "obligations": SOURCE["obligations"],
            "source_custody_record": SOURCE_RECORD}))
        outcome["recovery_initial_response"] = recovery_body
        recovery_id = recovery_body.get("call_id")
        if not recovery_id:
            outcome["recovery_terminal_response"] = recovery_body
        else:
            terminal = recovery_body
            end = time.monotonic() + 8
            poll_rows = []
            while terminal.get("status") == "pending" and time.monotonic() < end:
                start = time.monotonic_ns()
                terminal = public_body(await server.call_tool("interface_results", {
                    "call_id": recovery_id, "include_image": False}))
                poll_rows.append({"started_monotonic_ns": start,
                    "returned_monotonic_ns": time.monotonic_ns(),
                    "status": terminal.get("status"),
                    "release_confirmed": terminal.get("release_confirmed")})
                if terminal.get("status") == "pending":
                    await asyncio.sleep(.05)
            outcome["recovery_poll_rows"] = poll_rows
            outcome["recovery_terminal_response"] = terminal
        # The public recovery API is the only path allowed to resolve custody.
        _after_bytes, after = read_fence(fence_path)
        outcome["fence_after"] = after
        result = outcome["recovery_terminal_response"]
        receipt = result.get("recovery_receipt")
        if not isinstance(receipt, dict):
            receipt = (result.get("receipt") or {}).get("source", {}).get("raw_report", {}).get("recovery_receipt")
        outcome["recovery_receipt"] = receipt
        outcome["source_action_after"] = result.get("source_action") or result.get("source_action_status")
        outcome["source_operation_id_after"] = result.get("source_operation_id")
        outcome["source_target_generation_after"] = result.get("source_target_generation")
        outcome["public_task_success_after"] = result.get("task_success")
        outcome["public_replay_allowed_after"] = result.get("replay_allowed")
        if not isinstance(receipt, dict):
            raise RuntimeError("public recovery result omitted its native custody receipt")
        readback = receipt.get("readback") if isinstance(receipt.get("readback"), dict) else {}
        last_resolved = after["state"].get("last_resolved")
        required_fenced = {SOURCE["target_generation"], observed_generation}
        acceptance_checks = {
            "public_terminal_recovered": result.get("status") == "recovered"
                and result.get("recovery_status") == "recovered",
            "release_confirmed": result.get("release_confirmed") is True,
            "source_action_unknown": result.get("source_action_status") == "unknown",
            "source_identity_exact": receipt.get("operation_id") == SOURCE["operation_id"]
                and receipt.get("source_target_generation") == SOURCE["target_generation"],
            "recovery_generation_exact": receipt.get("recovery_target_generation") == observed_generation
                and receipt.get("target_generation") == SOURCE["target_generation"],
            "neutral_readback_bound": readback.get("operation_id") == SOURCE["operation_id"]
                and readback.get("source_target_generation") == SOURCE["target_generation"]
                and readback.get("target_generation") == observed_generation
                and readback.get("recovery_id") == receipt.get("recovery_id")
                and readback.get("neutral") is True
                and all(value is False for value in readback.get("key_button_states", [])),
            "horizon_verified": receipt.get("late_input_horizon_verified") is True
                and receipt.get("late_input_horizon_ns") >= 2_000_000_000
                and receipt.get("late_input_observation_count", 0) >= 2
                and type(receipt.get("late_input_max_observed_gap_ns")) is int
                and receipt["late_input_max_observed_gap_ns"]
                    <= receipt.get("late_input_max_sample_gap_ns", -1)
                and receipt.get("late_input_max_sample_gap_ns", 10**18) <= 100_000_000
                and receipt.get("late_input_observation_end_monotonic_ns", 0)
                    - receipt.get("late_input_release_received_monotonic_ns", 10**18)
                    >= 2_000_000_000,
            "no_task_success_or_replay": result.get("task_success") is None
                and result.get("replay_allowed") is False
                and result.get("operation_invoked") is False
                and result.get("next_action_requires_fresh_generation") is True,
            "fence_resolved_by_public_api": after["state"].get("status") == "clear"
                and after["state"].get("pending") is None
                and isinstance(last_resolved, dict)
                and last_resolved.get("operation_id") == SOURCE["operation_id"]
                and last_resolved.get("target_generation") == SOURCE["target_generation"]
                and required_fenced.issubset(set(after["state"].get("fenced_generations", []))),
            "no_fixture_task_effect": not effect_path.exists()
                and all(item.get("kind") == "ready" for item in
                    ([json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
                     if events_path.exists() else [])),
        }
        outcome["acceptance_checks"] = acceptance_checks
        if not all(acceptance_checks.values()):
            failed = [name for name, passed in acceptance_checks.items() if not passed]
            raise RuntimeError("R16 acceptance checks failed: " + ", ".join(failed))
        if outcome["public_recovery_attempt_count"] != 1:
            raise RuntimeError("recovery call count changed")
        # Read-only native proof after the API's release and configured horizon.
        backend = Win32Backend(targets)
        try:
            final_generation = backend.target_generation(TARGET)
            final_shift = backend._key_down_state(virtual_key("SHIFT"), TARGET)
            final_witness = list(backend._last_state_query_witness)
        finally:
            backend.close()
        outcome["native_recovery_target_after"] = {"target_generation": final_generation,
            "shift_down": final_shift, "state_query_witness": final_witness,
            "observed_monotonic_ns": time.monotonic_ns()}
        outcome["fixture_effect_present"] = effect_path.exists()
        outcome["fixture_events"] = ([json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            if events_path.exists() else [])
        outcome["native_final_neutral"] = (final_generation == observed_generation
            and final_shift is False)
        outcome["acceptance_checks"]["native_final_neutral"] = outcome["native_final_neutral"]
        outcome["classification"] = "RECOVERY_GATES_PASS_PENDING_CLEANUP"
        should_preserve_fixture = False
    except Exception as error:
        outcome["classification"] = "FAIL_OR_UNKNOWN_FENCE_RETAINED"
        outcome["error_type"] = type(error).__name__
        outcome["error"] = str(error)
    finally:
        if server is not None:
            try:
                outcome["server_close"] = public_body(await server.call_tool("interface_close", {}))
            except Exception as error:
                outcome["server_close_error"] = f"{type(error).__name__}: {error}"
        if fixture is not None and not should_preserve_fixture:
            if fixture.poll() is None:
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
                try:
                    fixture.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    outcome["fixture_close_timeout"] = True
            outcome["fixture_exit_code"] = fixture.poll()
        current_foreground = int(user32.GetForegroundWindow() or 0)
        restored = False
        if original_foreground and user32.IsWindow(original_foreground):
            restored = bool(user32.SetForegroundWindow(original_foreground))
        outcome["foreground_restore"] = {"original_hwnd": original_foreground,
            "before_restore_hwnd": current_foreground,
            "set_foreground_returned": restored,
            "after_restore_hwnd": int(user32.GetForegroundWindow() or 0),
            "observed_monotonic_ns": time.monotonic_ns()}
        if outcome.get("classification") == "RECOVERY_GATES_PASS_PENDING_CLEANUP":
            cleanup_checks = {
                "foreground_restored": (original_foreground == 0
                    or outcome["foreground_restore"]["after_restore_hwnd"] == original_foreground),
                "fixture_exited_cleanly": outcome.get("fixture_exit_code") == 0,
                "native_final_neutral": outcome.get("native_recovery_target_after", {}).get(
                    "target_generation") == outcome.get("recovery_generation")
                    and outcome.get("native_recovery_target_after", {}).get("shift_down") is False,
            }
            outcome["cleanup_checks"] = cleanup_checks
            outcome["acceptance_checks"].update(cleanup_checks)
            outcome["classification"] = ("PASS_SCOPED_ORPHAN_RECOVERY_WITH_HORIZON"
                if all(cleanup_checks.values()) else "FAIL_OR_UNKNOWN_CLEANUP_GATE")
        outcome["finished_monotonic_ns"] = time.monotonic_ns()
        save(RUN / "result.json", outcome)
        write_manifest(RUN, "SHA256SUMS")
    if outcome.get("classification") != "PASS_SCOPED_ORPHAN_RECOVERY_WITH_HORIZON":
        raise RuntimeError("R16 failed or remained unresolved; inspect retained result")
    return outcome


if __name__ == "__main__":
    result = asyncio.run(run())
    print(json.dumps({"classification": result["classification"],
        "recovery_generation": result.get("recovery_generation"),
        "result": str(RUN / "result.json")}, sort_keys=True))

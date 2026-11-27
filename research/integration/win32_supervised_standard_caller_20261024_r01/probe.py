"""One-shot public stdio-MCP trial of the supervised native Win32 caller."""
from __future__ import annotations

import asyncio
import base64
import ctypes
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
RAW = PACKET / "raw.json"
CONDITIONS = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
record = {
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": None,
    "source_tracked_tree_clean": None,
    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "caller_kind": "mcp_stdio",
    "session_mode": "supervised-win32",
    "dispatch_attempts": 0,
    "probe_status": "UNKNOWN",
}
children = []
logs = []
sys.path.insert(0, str(ROOT))
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetForegroundWindow.restype = ctypes.c_void_p
user32.IsWindow.argtypes = [ctypes.c_void_p]
user32.IsWindow.restype = ctypes.c_int
user32.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                ctypes.c_size_t, ctypes.c_ssize_t]
user32.PostMessageW.restype = ctypes.c_int
user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
user32.SetForegroundWindow.restype = ctypes.c_int


def parse_response(reply):
    item = next(block for block in reply.content
                if getattr(block, "type", None) == "text")
    return json.loads(item.text)


def save_content(blocks):
    content = []
    for block in blocks:
        kind = getattr(block, "type", None)
        if kind == "text":
            content.append({"type": "text", "text": block.text})
        elif kind == "image":
            data = block.data
            content.append({"type": "image", "mimeType": block.mimeType,
                            "data_b64": data if isinstance(data, str)
                            else base64.b64encode(data).decode("ascii")})
        else:
            content.append({"type": str(kind), "repr": repr(block)})
    return content


def source_preflight():
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tracked = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=ROOT, text=True).strip()
    record["source_commit"] = commit
    record["source_tracked_tree_clean"] = not tracked
    if commit != CONDITIONS["source_commit"] or tracked:
        raise RuntimeError("source commit mismatch or tracked source is dirty")


def client_rect(hwnd):
    from ctypes import wintypes
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetClientRect.restype = wintypes.BOOL
    rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise OSError(ctypes.get_last_error(), "GetClientRect")
    width, height = int(rect.right - rect.left), int(rect.bottom - rect.top)
    if width <= 70 or height <= 70:
        raise RuntimeError("owned fixture client area is too small for frozen click")
    return {"left": int(rect.left), "top": int(rect.top),
            "right": int(rect.right), "bottom": int(rect.bottom),
            "width": width, "height": height}


def start_fixture():
    folder = RUN / "fixture"
    folder.mkdir(parents=True)
    meta, effect, events = (folder / name for name in
                            ("fixture-meta.json", "effect.json", "events.jsonl"))
    log_path = folder / "fixture.log"
    log = log_path.open("wb")
    logs.append(log)
    process = subprocess.Popen(
        [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
         "--meta", str(meta), "--effect", str(effect), "--events", str(events)],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    row = {"pid": process.pid, "meta_path": str(meta), "effect_path": str(effect),
           "events_path": str(events), "log_path": str(log_path)}
    children.append((process, row))
    deadline = time.monotonic() + CONDITIONS["timeouts_seconds"]["fixture_ready"]
    while time.monotonic() < deadline and not meta.exists():
        if process.poll() is not None:
            raise RuntimeError(f"owned fixture exited before ready: {process.returncode}")
        time.sleep(0.025)
    if not meta.exists():
        raise TimeoutError("owned fixture did not become ready")
    row["meta"] = json.loads(meta.read_text(encoding="utf-8"))
    row["hwnd"] = int(row["meta"]["hwnd"])
    from runtime.backends.win32_v1.backend import Win32Backend
    backend = Win32Backend({"fixture": row["hwnd"]})
    try:
        row["target_identity"] = {
            "owner": backend._window_owner_identity_for_hwnd(row["hwnd"]),
            "generation": backend.target_generation("fixture"),
        }
    finally:
        backend.close()
    row["client_rect"] = client_rect(row["hwnd"])
    if row["target_identity"]["owner"]["pid"] != process.pid:
        raise RuntimeError("fixture HWND owner did not match the owned process")
    return process, row


def close_fixture(process, row):
    hwnd = row.get("hwnd")
    row["close_posted"] = bool(hwnd is not None
        and user32.PostMessageW(hwnd, 0x0010, 0, 0))
    try:
        process.wait(timeout=CONDITIONS["timeouts_seconds"]["fixture_close"])
    except subprocess.TimeoutExpired:
        row["terminate_attempted"] = True
        process.terminate()
        try:
            process.wait(timeout=CONDITIONS["timeouts_seconds"]["owned_process_terminate"])
        except subprocess.TimeoutExpired:
            row["kill_attempted"] = True
            process.kill()
            process.wait(timeout=CONDITIONS["timeouts_seconds"]["owned_process_terminate"])
    row["exit_code"] = process.returncode
    row["window_exists_after_exit"] = bool(user32.IsWindow(hwnd)) if hwnd else None
    event_path = Path(row["events_path"])
    row["events"] = ([json.loads(line) for line in
        event_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if event_path.exists() else [])
    effect_path = Path(row["effect_path"])
    row["effect"] = (json.loads(effect_path.read_text(encoding="utf-8"))
        if effect_path.exists() else None)


def restore_foreground(hwnd):
    exists = bool(hwnd and user32.IsWindow(hwnd))
    if not exists:
        return {"attempted": False, "restored": False,
                "prior_hwnd_exists": False,
                "reason": "prior_window_unavailable"}
    set_result = bool(user32.SetForegroundWindow(hwnd))
    observed = int(user32.GetForegroundWindow() or 0)
    return {"attempted": True, "prior_hwnd_exists": True,
            "set_foreground_return": set_result,
            "observed_hwnd": observed, "restored": observed == int(hwnd)}


async def run_public_calls(targets_path, fixture_row):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    calls_path = RUN / "calls"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets_path),
              "--output-directory", str(calls_path),
              "--session-mode", "supervised-win32"],
        cwd=str(ROOT))
    timeout = CONDITIONS["timeouts_seconds"]
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await asyncio.wait_for(client.initialize(), timeout["mcp_initialize"])
            tools = await asyncio.wait_for(client.list_tools(), timeout["mcp_initialize"])
            record["tools"] = sorted(tool.name for tool in tools.tools)
            clock_reply = await asyncio.wait_for(
                client.call_tool("interface_clock", {}), timeout["mcp_initialize"])
            clock_body = parse_response(clock_reply)
            record["clock"] = clock_body
            observed = await asyncio.wait_for(client.call_tool("interface_observe", {
                "target": "fixture", "frame": "window_client",
                "region": [0, 0, fixture_row["client_rect"]["width"],
                            fixture_row["client_rect"]["height"]]}),
                timeout["observe"])
            observe_body = parse_response(observed)
            raw_observation = (observe_body.get("receipt", {}).get("source", {})
                               .get("raw_report", {}))
            record["public_observation"] = {
                "is_error": observed.isError, "response": observe_body,
                "raw_report": raw_observation,
                "content": save_content(observed.content)}
            generation = raw_observation.get("target_generation")
            if not isinstance(generation, str):
                raise RuntimeError("public observation did not return target_generation")

            trial = CONDITIONS["trial"]
            program = {
                "schema": "agent-interface/program-v1",
                "program_id": trial["program_id"],
                "source": {
                    "observation_seq": trial["admission"]["observation_seq"],
                    "binding_revision": trial["admission"]["binding_revision"],
                    "target_generations": {"fixture": generation},
                },
                "authority": {
                    "lease_id": "supervised-standard-effect-r01",
                    "expires_at_ns": clock_body["monotonic_ns"] + 60_000_000_000,
                },
                "terminal": {"release_all_required": True},
                "ops": trial["operations"],
            }
            record["program"] = program
            validation = await asyncio.wait_for(
                client.call_tool("interface_validate", {"program": program}),
                timeout["validate"])
            record["public_validation"] = {
                "is_error": validation.isError,
                "response": parse_response(validation),
                "content": save_content(validation.content)}
            if (validation.isError
                    or record["public_validation"]["response"].get("static_valid") is not True):
                return

            record["dispatch_attempts"] = 1
            dispatch_start = time.perf_counter_ns()
            dispatched = await asyncio.wait_for(client.call_tool("interface_dispatch", {
                "program": program,
                "current_observation_seq": trial["admission"]["observation_seq"],
                "current_binding_revision": trial["admission"]["binding_revision"],
                "wait_for_result_ms": 10000,
            }), timeout["dispatch_response"])
            dispatch_end = time.perf_counter_ns()
            dispatch_body = parse_response(dispatched)
            call_id = dispatch_body.get("call_id")
            record["public_dispatch"] = {
                "is_error": dispatched.isError,
                "started_monotonic_ns": dispatch_start,
                "returned_monotonic_ns": dispatch_end,
                "response": dispatch_body,
                "content": save_content(dispatched.content),
            }
            deadline = time.monotonic() + timeout["result_readback"]
            result_responses = []
            while isinstance(call_id, str) and time.monotonic() < deadline:
                result_reply = await asyncio.wait_for(
                    client.call_tool("interface_results", {"call_id": call_id}), 5)
                result_body = parse_response(result_reply)
                result_responses.append({"is_error": result_reply.isError,
                                         "response": result_body})
                row = result_body.get("result") if isinstance(
                    result_body.get("result"), dict) else result_body
                if row.get("action", {}).get("status") in (
                        "completed", "recovered", "unknown"):
                    break
                await asyncio.sleep(0.05)
            record["result_readbacks"] = result_responses
            call_dir = calls_path / str(call_id) if call_id else None
            report_path = call_dir / "report.json" if call_dir else None
            record["retained_report"] = (
                json.loads(report_path.read_text(encoding="utf-8"))
                if report_path is not None and report_path.exists() else None)

            effect_path = Path(fixture_row["effect_path"])
            readback_deadline = time.monotonic() + timeout["effect_readback"]
            while time.monotonic() < readback_deadline and not effect_path.exists():
                await asyncio.sleep(0.02)
            record["effect_readback"] = (
                json.loads(effect_path.read_text(encoding="utf-8"))
                if effect_path.exists() else None)
            close_reply = await asyncio.wait_for(
                client.call_tool("interface_close", {}),
                timeout["dispatch_response"])
            record["public_close"] = {
                "is_error": close_reply.isError,
                "response": parse_response(close_reply),
                "content": save_content(close_reply.content),
            }
            session_id = ((record.get("retained_report") or {}).get("session") or {}).get(
                "session_id")
            close_report_path = (calls_path / f"session-{session_id}-close.json"
                                 if isinstance(session_id, str) else None)
            record["session_close_report"] = (
                json.loads(close_report_path.read_text(encoding="utf-8"))
                if close_report_path is not None and close_report_path.exists() else None)


def main():
    if sys.platform != "win32":
        raise SystemExit("native Win32 attempt requires Windows")
    source_preflight()
    for path in (RUN, RAW, PACKET / "audit.json", PACKET / "SHA256SUMS"):
        if path.exists():
            raise SystemExit(f"one-shot output already exists; refusing to overwrite: {path}")
    if not CONDITIONS["trial"]["operations"]:
        raise SystemExit("frozen input program unexpectedly empty")
    RUN.mkdir()
    process = None
    fixture = None
    previous_foreground = int(user32.GetForegroundWindow() or 0)
    record["previous_foreground_hwnd"] = previous_foreground
    try:
        process, fixture = start_fixture()
        record["fixture"] = fixture
        targets = RUN / "targets.json"
        targets.write_text(json.dumps({"fixture": fixture["hwnd"]}, sort_keys=True)
                           + "\n", encoding="utf-8")
        asyncio.run(asyncio.wait_for(
            run_public_calls(targets, fixture),
            CONDITIONS["timeouts_seconds"]["attempt_total"]))
        effect_deadline = time.monotonic() + CONDITIONS["timeouts_seconds"]["effect_readback"]
        effect_path = Path(fixture["effect_path"])
        while time.monotonic() < effect_deadline and not effect_path.exists():
            time.sleep(0.02)
        close_fixture(process, fixture)
        record["probe_status"] = ("completed_with_independent_effect"
            if fixture.get("effect") == CONDITIONS["trial"]["expected_effect"]
            else "completed_without_expected_effect")
    except BaseException as error:
        record["error"] = {"type": type(error).__name__, "detail": str(error)}
        record["probe_status"] = "FAIL_OR_UNKNOWN"
        for owned_process, owned_row in children:
            if owned_process.poll() is None:
                try:
                    close_fixture(owned_process, owned_row)
                except BaseException as cleanup_error:
                    record["cleanup_error"] = {
                        "type": type(cleanup_error).__name__,
                        "detail": str(cleanup_error)}
    finally:
        if children:
            record["foreground_restore"] = restore_foreground(previous_foreground)
        record["ended_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        RAW.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False)
                       + "\n", encoding="utf-8")
        for log in logs:
            log.close()


if __name__ == "__main__":
    raise SystemExit(main())

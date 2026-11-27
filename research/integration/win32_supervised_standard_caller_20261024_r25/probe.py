"""One-shot public stdio-MCP Win32 fixture trial with an independent file oracle."""
from __future__ import annotations

import asyncio
import ctypes
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from ctypes import wintypes

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from runtime.backends.win32_v1.backend import Win32Backend

RAW = ROOT / "raw.json"
RUN = ROOT / "run"
CONDITIONS = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
if RAW.exists() or RUN.exists():
    raise SystemExit("frozen output exists; refusing to repeat this trial")
if sys.platform != "win32":
    raise SystemExit("live trial requires Windows")

TEXT = CONDITIONS["trial"]["expected_effect"]["text"]
record = {
    "schema": "win32-supervised-standard-caller-r25-receipt-v1",
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": os.environ.get("SOURCE_COMMIT", CONDITIONS["source_commit"]),
    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "caller_kind": "mcp_stdio",
    "session_mode": "supervised-win32",
    "predecessor": CONDITIONS["predecessor"],
    "listed_tools": [],
    "dispatch_attempts": 0,
    "status": "UNKNOWN",
    "oracle": {"nonclaims": CONDITIONS["nonclaims"]},
}
clock_info = time.get_clock_info("perf_counter")
record["timing_clock"] = {
    "implementation": clock_info.implementation,
    "resolution_seconds": clock_info.resolution,
    "monotonic": clock_info.monotonic,
    "adjustable": clock_info.adjustable,
}
fixture = None
hwnd = None
fixture_meta = RUN / "fixture-meta.json"
effect_path = RUN / "effect.json"
events_path = RUN / "events.jsonl"
targets_path = RUN / "targets.json"
calls_path = RUN / "mcp-calls"


def save_content(blocks):
    rows = []
    for block in blocks:
        kind = getattr(block, "type", None)
        if kind == "text":
            rows.append({"type": "text", "text": block.text})
        elif kind == "image":
            import base64
            rows.append({"type": "image", "mimeType": block.mimeType,
                         "data_b64": block.data if isinstance(block.data, str) else base64.b64encode(block.data).decode("ascii")})
        else:
            rows.append({"type": str(kind), "repr": repr(block)})
    return rows


async def mcp_trial(targets, hwnd_value):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets),
              "--output-directory", str(calls_path),
              "--session-mode", "supervised-win32"],
        cwd=str(REPO_ROOT),
    )
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await asyncio.wait_for(client.initialize(), timeout=10)
            listed = await asyncio.wait_for(client.list_tools(), timeout=10)
            record["listed_tools"] = sorted(tool.name for tool in listed.tools)
            observation_start = time.perf_counter_ns()
            observation = await asyncio.wait_for(client.call_tool(
                "interface_observe", {"target": "fixture", "frame": "window_client",
                                       "region": record["observation_region"]}), timeout=15)
            observation_return = time.perf_counter_ns()
            record["observation"] = {
                "started_monotonic_ns": observation_start,
                "returned_monotonic_ns": observation_return,
                "is_error": observation.isError,
                "content": save_content(observation.content),
            }
            observation_payload = json.loads(next(block.text for block in observation.content
                if getattr(block, "type", None) == "text"))
            generation = (observation_payload.get("receipt", {}).get("source", {})
                .get("raw_report", {}).get("target_generation"))
            record["observed_target_generation"] = generation
            observation_raw = observation_payload.get("receipt", {}).get("source", {}).get("raw_report", {})
            record["observation_target_generation_consistency"] = observation_raw.get("target_generation_consistency")
            if (not isinstance(generation, str) or len(generation) != 64
                    or observation_raw.get("target_generation_consistency") != "matched"
                    or generation != record.get("target_identity_before", {}).get("generation")
                    or generation == CONDITIONS["predecessor"]["target_generation"]):
                raise RuntimeError("public observation did not return a distinct, matched fresh target_generation")
            program_id = CONDITIONS["trial"]["program_id"]
            observation_seq = CONDITIONS["trial"]["admission"]["observation_seq"]
            binding_revision = CONDITIONS["trial"]["admission"]["binding_revision"]
            program = {
                "schema": "agent-interface/program-v1",
                "program_id": program_id,
                "source": {"observation_seq": observation_seq,
                           "binding_revision": binding_revision,
                           "target_generations": {"fixture": generation}},
                "authority": {"lease_id": CONDITIONS["trial"]["lease_id"],
                    "expires_at_ns": time.monotonic_ns() +
                        CONDITIONS["trial"]["lease_duration_seconds"] * 1_000_000_000},
                "terminal": {"release_all_required": True},
                "ops": [
                    {"op": "focus", "target": "fixture"},
                    {"op": "pointer_move", "frame": "window_client", "x": 70, "y": 70},
                    {"op": "pointer_button", "button": "left", "down": True},
                    {"op": "pointer_button", "button": "left", "down": False},
                    {"op": "wait_update", "timeout_ms": 40},
                    {"op": "text", "text": TEXT},
                    {"op": "key_chord", "keys": ["CTRL", "S"]},
                    {"op": "wait_update", "timeout_ms": 40},
                    {"op": "observe", "frame": "window_client",
                        "x": 0, "y": 0,
                        "w": record["observation_region"][2],
                        "h": record["observation_region"][3]},
                    {"op": "release_all"},
                ],
            }
            record["program"] = program
            validation = await asyncio.wait_for(client.call_tool(
                "interface_validate", {"program": program}), timeout=10)
            try:
                record["program_validation"] = json.loads(next(
                    block.text for block in validation.content
                    if getattr(block, "type", None) == "text"))
            except Exception as exc:
                record["program_validation"] = {"parse_error": repr(exc)}
            if validation.isError or record["program_validation"].get("static_valid") is not True:
                record["dispatch_attempts"] = 0
                return
            record["dispatch_attempts"] = 1
            dispatch_start = time.perf_counter_ns()
            dispatch = await asyncio.wait_for(client.call_tool(
                "interface_dispatch", {"program": program,
                    "current_observation_seq": observation_seq,
                    "current_binding_revision": binding_revision,
                    "wait_for_result_ms": CONDITIONS["trial"]["wait_for_result_ms"]}), timeout=25)
            dispatch_return = time.perf_counter_ns()
            record["dispatch"] = {
                "started_monotonic_ns": dispatch_start,
                "returned_monotonic_ns": dispatch_return,
                "is_error": dispatch.isError,
                "content": save_content(dispatch.content),
            }
            try:
                response = json.loads(next(block.text for block in dispatch.content
                                           if getattr(block, "type", None) == "text"))
            except Exception as exc:
                record["response_parse_error"] = repr(exc)
                return
            record["public_response"] = response
            call_id = response.get("call_id")
            if isinstance(call_id, str):
                report_file = calls_path / call_id / "report.json"
                if report_file.exists():
                    record["retained_report"] = json.loads(report_file.read_text(encoding="utf-8"))
            close = await asyncio.wait_for(client.call_tool("interface_close", {}), timeout=5)
            record["public_close"] = {
                "is_error": close.isError,
                "content": save_content(close.content),
            }
            try:
                record["public_close"]["response"] = json.loads(next(
                    block.text for block in close.content
                    if getattr(block, "type", None) == "text"))
            except Exception as exc:
                record["public_close"]["response_parse_error"] = repr(exc)


def target_identity(hwnd_value):
    backend = Win32Backend({"fixture": hwnd_value})
    return {"owner": backend._window_owner_identity_for_hwnd(hwnd_value),
            "generation": backend.target_generation("fixture")}


def main():
    global fixture, hwnd
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    record["previous_foreground_hwnd"] = int(user32.GetForegroundWindow() or 0)
    RUN.mkdir()
    try:
        fixture = subprocess.Popen([
            sys.executable, str(ROOT / "fixture_app.py"),
            "--meta", str(fixture_meta), "--effect", str(effect_path),
            "--events", str(events_path),
        ], cwd=str(REPO_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
           text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        record["fixture_pid"] = fixture.pid
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not fixture_meta.exists():
            if fixture.poll() is not None:
                record["fixture_stderr"] = fixture.stderr.read() if fixture.stderr else ""
                raise RuntimeError("owned fixture exited before ready")
            time.sleep(0.05)
        if not fixture_meta.exists():
            raise TimeoutError("fixture readiness exceeded 10s")
        fixture_info = json.loads(fixture_meta.read_text(encoding="utf-8"))
        hwnd = int(fixture_info["hwnd"])
        record["fixture_hwnd"] = hwnd
        record["target_identity_before"] = target_identity(hwnd)
        if (record["target_identity_before"]["owner"]["pid"] != fixture.pid or
                record["target_identity_before"]["generation"] ==
                CONDITIONS["predecessor"]["target_generation"]):
            raise RuntimeError("new fixture owner/generation did not differ from recovered predecessor")
        targets_path.write_text(json.dumps({"fixture": hwnd}, sort_keys=True) + "\n",
                                encoding="utf-8")
        client_rect = wintypes.RECT()
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user32.GetClientRect.restype = wintypes.BOOL
        if not user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
            raise OSError(ctypes.get_last_error(), "GetClientRect")
        client_width = int(client_rect.right - client_rect.left)
        client_height = int(client_rect.bottom - client_rect.top)
        if client_width <= 0 or client_height <= 0:
            raise RuntimeError("owned fixture reported an empty client rectangle")
        record["client_rect"] = {
            "left": int(client_rect.left), "top": int(client_rect.top),
            "right": int(client_rect.right), "bottom": int(client_rect.bottom),
            "width": client_width, "height": client_height,
        }
        record["observation_region"] = [0, 0, client_width, client_height]
        asyncio.run(mcp_trial(targets_path, hwnd))
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and not effect_path.exists():
            time.sleep(0.01)
        if effect_path.exists():
            record["effect_read_started_monotonic_ns"] = time.perf_counter_ns()
            record["effect_file"] = json.loads(effect_path.read_text(encoding="utf-8"))
            record["effect_read_returned_monotonic_ns"] = time.perf_counter_ns()
            record["effect_mtime_ns"] = effect_path.stat().st_mtime_ns
        if events_path.exists():
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            record["fixture_events"] = events
            chars = [event for event in events if event.get("kind") == "char"]
            saves = [event for event in events if event.get("kind") == "save"]
            record["oracle"].update(
                task_pass=(record.get("effect_file") ==
                           {"saved": True, "text": TEXT, "clicked": True}),
                expected_char_event_count=len(TEXT),
                char_event_count=len(chars),
                save_event_count=len(saves),
                event_text="".join(chr(event["code"]) for event in chars),
            )
            record["oracle"]["event_text_matches"] = record["oracle"]["event_text"] == TEXT
            saves = [event for event in events if event.get("kind") == "save"]
            dispatch = record.get("dispatch", {})
            if len(saves) == 1 and dispatch:
                dispatch_start = dispatch.get("started_monotonic_ns")
                dispatch_return = dispatch.get("returned_monotonic_ns")
                commit_start = saves[0].get("commit_started_monotonic_ns")
                commit_done = saves[0].get("commit_completed_monotonic_ns")
                read_start = record.get("effect_read_started_monotonic_ns")
                read_done = record.get("effect_read_returned_monotonic_ns")
                record["timing"] = {
                    "dispatch_to_save_commit_ms": (commit_done - dispatch_start) / 1_000_000,
                    "save_write_ms": (commit_done - commit_start) / 1_000_000,
                    "dispatch_to_public_return_ms": (dispatch_return - dispatch_start) / 1_000_000,
                    "commit_to_independent_readback_ms": (read_start - commit_done) / 1_000_000,
                    "independent_read_duration_ms": (read_done - read_start) / 1_000_000,
                    "dispatch_start_monotonic_ns": dispatch_start,
                    "dispatch_return_monotonic_ns": dispatch_return,
                    "commit_start_monotonic_ns": commit_start,
                    "commit_done_monotonic_ns": commit_done,
                    "read_start_monotonic_ns": read_start,
                    "read_done_monotonic_ns": read_done,
                    "release_timing_interpretation": "actual release receipt timestamp is recorded separately from the public dispatch response",
                }
        record["target_identity_after"] = target_identity(hwnd)
        report = record.get("retained_report", {})
        execution = report.get("result", {}).get("execution", {})
        releases = execution.get("releases", [])
        release = releases[-1] if releases else {}
        if release.get("monotonic_ns") is not None and record.get("timing"):
            record["timing"]["release_receipt_monotonic_ns"] = release["monotonic_ns"]
            record["timing"]["dispatch_to_release_receipt_ms"] = (
                release["monotonic_ns"] - record["timing"]["dispatch_start_monotonic_ns"]
            ) / 1_000_000
        record["oracle"].update(
            release_receipt=release,
            release_pass=(release.get("verified") is True
                and release.get("keys_down") == []
                and release.get("buttons_down") == []
                and release.get("keys_unknown") == []
                and release.get("buttons_unknown") == []),
            runtime_completed=(report.get("result", {}).get("status") == "completed"),
            runtime_task_success_null=(report.get("result", {}).get("task_success") is None),
            new_generation=(record.get("target_identity_before", {}).get("generation") !=
                CONDITIONS["predecessor"]["target_generation"]),
            fresh_public_generation=(record.get("observed_target_generation") ==
                record.get("target_identity_before", {}).get("generation")),
            public_close=(record.get("public_close", {}).get("response", {}).get("status") == "closed"),
        )
        record["status"] = (
            "PASS" if record["oracle"].get("task_pass") is True
            and record["oracle"].get("event_text_matches") is True
            and record["oracle"].get("char_event_count") == len(TEXT)
            and record["oracle"].get("save_event_count") == 1
            and record["oracle"].get("release_pass") is True
            and record["oracle"].get("runtime_completed") is True
            and record["oracle"].get("runtime_task_success_null") is True
            and record["oracle"].get("new_generation") is True
            and record["oracle"].get("fresh_public_generation") is True
            and record["oracle"].get("public_close") is True
            and record.get("timing", {}).get("commit_done_monotonic_ns", 0)
                <= record.get("timing", {}).get("dispatch_return_monotonic_ns", -1)
            and record.get("timing", {}).get("read_start_monotonic_ns", 0)
                >= record.get("timing", {}).get("commit_done_monotonic_ns", 1)
            else "FAIL_OR_UNKNOWN")
    except BaseException as exc:
        record["status"] = "UNKNOWN"
        record["error_type"] = type(exc).__name__
        record["error"] = str(exc)
    finally:
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostMessageW.restype = wintypes.BOOL
        if hwnd:
            record["fixture_close_posted"] = bool(user32.PostMessageW(hwnd, 0x0010, 0, 0))
        else:
            record["fixture_close_posted"] = False
        if fixture is not None:
            try:
                fixture.wait(timeout=5)
            except subprocess.TimeoutExpired:
                record["fixture_terminate_attempted"] = True
                fixture.terminate()
                try:
                    fixture.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    record["fixture_kill_attempted"] = True
                    fixture.kill()
                    fixture.wait(timeout=2)
            record["fixture_exit_code"] = fixture.returncode
            if fixture.stderr:
                record["fixture_stderr"] = fixture.stderr.read()
                fixture.stderr.close()
        previous = record.get("previous_foreground_hwnd", 0)
        if previous and user32.IsWindow(previous):
            record["foreground_restore"] = {
                "attempted": True,
                "set_foreground_return": bool(user32.SetForegroundWindow(previous)),
                "observed_hwnd": int(user32.GetForegroundWindow() or 0),
            }
        else:
            record["foreground_restore"] = {
                "attempted": False,
                "reason": "previous foreground window absent",
                "observed_hwnd": int(user32.GetForegroundWindow() or 0),
            }
        record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        RAW.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    if record["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Execute exactly one frozen, fixture-only public-MCP task-oracle trial."""
from __future__ import annotations
import asyncio
import base64
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run" / "phase2_task"
COND = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
TOKEN = COND["phase2_task"]["token"]
ORACLE_ID = COND["phase2_task"]["oracle_id"]
EXPECTED = COND["phase2_task"]["expected_effect"]
ATTEMPT = COND["attempt_id"]

def save_json(path: Path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def result_text(reply):
    return next((item.text for item in reply.content if getattr(item, "type", None) == "text"), "")

def find_first(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = find_first(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_first(value, key)
            if found is not None:
                return found
    return None

def find_action(obj):
    if isinstance(obj, dict):
        candidate = obj.get("action")
        if isinstance(candidate, dict) and isinstance(candidate.get("status"), str):
            return candidate
        for value in obj.values():
            found = find_action(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_action(value)
            if found is not None:
                return found
    return None

def record_reply(name, reply):
    parsed = None
    body = result_text(reply)
    try:
        parsed = json.loads(body)
    except Exception:
        pass
    blocks = []
    for index, item in enumerate(reply.content):
        kind = getattr(item, "type", "unknown")
        if kind == "image":
            raw = base64.b64decode(item.data)
            destination = RUN / f"{name}-{index}.png"
            destination.write_bytes(raw)
            blocks.append({"type": "image", "path": str(destination),
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "mimeType": item.mimeType})
        elif kind == "text":
            destination = RUN / f"{name}-{index}.json"
            destination.write_text(item.text + "\n", encoding="utf-8")
            blocks.append({"type": "text", "path": str(destination),
                "sha256": hashlib.sha256(item.text.encode("utf-8")).hexdigest()})
    return {"isError": reply.isError, "parsed": parsed, "blocks": blocks}

def fg_info(hwnd):
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(ctypes.c_void_p(hwnd), buf, len(buf))
    return {"hwnd": int(hwnd), "title": buf.value,
        "is_window": bool(user32.IsWindow(ctypes.c_void_p(hwnd)))}

async def main():
    RUN.mkdir(parents=True, exist_ok=True)
    prior = [path.name for path in RUN.iterdir() if path.name != "harness-preflight-failure.json"]
    if prior:
        raise RuntimeError(f"run output already contains evidence: {prior}")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    original_foreground = int(user32.GetForegroundWindow() or 0)
    save_json(RUN / "preflight.json", {
        "attempt_id": ATTEMPT, "host": os.environ.get("COMPUTERNAME"),
        "python": sys.version, "original_foreground": fg_info(original_foreground) if original_foreground else None,
        "started_unix_ns": time.time_ns(), "source_commit": COND["source_commit"],
        "conditions_sha256": hashlib.sha256((PACKET / "conditions.json").read_bytes()).hexdigest()})
    fixture_cmd = [sys.executable, str(PACKET / "fixture_app_timed.py"),
        "--meta", str(RUN / "fixture-meta.json"), "--effect", str(RUN / "effect.json"),
        "--events", str(RUN / "fixture-events.jsonl")]
    fixture = subprocess.Popen(fixture_cmd, cwd=ROOT,
        stdout=(RUN / "fixture.stdout.bin").open("wb"),
        stderr=(RUN / "fixture.stderr.bin").open("wb"))
    server_proc = None
    meta = {}
    outcome = {"attempt_id": ATTEMPT, "status": "FAIL_OR_UNKNOWN", "steps": [],
        "fixture_pid": fixture.pid, "started_monotonic_ns": time.monotonic_ns()}
    try:
        deadline = time.monotonic() + 10
        while not (RUN / "fixture-meta.json").exists() and fixture.poll() is None and time.monotonic() < deadline:
            await asyncio.sleep(0.05)
        if fixture.poll() is not None or not (RUN / "fixture-meta.json").exists():
            raise RuntimeError("fixture failed to become ready")
        meta = json.loads((RUN / "fixture-meta.json").read_text(encoding="utf-8"))
        targets = RUN / "targets.json"
        save_json(targets, {"fixture": meta["hwnd"]})
        params = StdioServerParameters(command=sys.executable, cwd=str(ROOT), args=[
            str(PACKET / "server_with_oracle.py"), str(ROOT), str(targets),
            str(RUN / "server-receipts"), str(RUN / "effect.json"),
            str(RUN / "oracle-evidence.json"), ORACLE_ID, TOKEN,
            str(RUN / "fixture-events.jsonl")])
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                tools = await client.list_tools()
                names = sorted(tool.name for tool in tools.tools)
                save_json(RUN / "tools.json", {"tool_names": names})
                if "interface_verify_task" not in names:
                    raise RuntimeError("server did not expose task oracle")

                obs = await client.call_tool("interface_observe", {
                    "target": "fixture", "frame": "window_client", "region": [0, 0, 400, 180]})
                obs_record = record_reply("observe", obs)
                outcome["steps"].append({"name": "observation", **obs_record})
                report = obs_record["parsed"] or {}
                generation = find_first(report, "target_generation")
                if not isinstance(generation, str) or len(generation) != 64:
                    raise RuntimeError("observation lacked a 64-hex target_generation")
                int(generation, 16)

                clock_reply = await client.call_tool("interface_clock", {})
                clock_rec = record_reply("clock", clock_reply)
                outcome["steps"].append({"name": "clock", **clock_rec})
                clock = (clock_rec.get("parsed") or {}).get("monotonic_ns")
                if type(clock) is not int:
                    raise RuntimeError("execution-host clock unavailable")
                program = {"schema": "agent-interface/program-v1",
                    "program_id": "win32-r38d-timestamped-task-effect",
                    "source": {"observation_seq": 1, "binding_revision": 1,
                        "target_generations": {"fixture": generation}},
                    "authority": {"lease_id": "win32-r37b-fresh-generation-task-lease",
                        "expires_at_ns": clock + 45_000_000_000},
                    "terminal": {"release_all_required": True},
                    "ops": COND["phase2_protocol"]["exact_program"]}
                validation = await client.call_tool("interface_validate", {"program": program})
                valid_record = record_reply("validation", validation)
                outcome["steps"].append({"name": "validation", **valid_record})
                if validation.isError or (valid_record.get("parsed") or {}).get("static_valid") is not True:
                    raise RuntimeError("exact frozen program failed static validation")

                dispatch_started_ns = time.monotonic_ns()
                dispatch = await client.call_tool("interface_dispatch", {
                    "program": program, "current_observation_seq": 1,
                    "current_binding_revision": 1,
                    "wait_for_result_ms": COND["phase2_protocol"]["dispatch_response_wait_ms"]})
                dispatch_returned_ns = time.monotonic_ns()
                dispatch_record = record_reply("dispatch", dispatch)
                dispatch_record["client_timing_ns"] = {"started": dispatch_started_ns, "returned": dispatch_returned_ns}
                outcome["steps"].append({"name": "dispatch", **dispatch_record})
                dispatch_report = dispatch_record.get("parsed") or {}
                call_id = find_first(dispatch_report, "call_id")
                action_status = find_first(dispatch_report, "status")
                if dispatch.isError or not isinstance(call_id, str) or len(call_id) != 32:
                    raise RuntimeError("dispatch did not return one action call ID")
                action = find_action(dispatch_report) or (dispatch_report.get("result") if isinstance(dispatch_report.get("result"), dict) else {})
                if action_status == "pending":
                    # Read the exact retained call only. This does not re-dispatch input.
                    stop_at = time.monotonic() + COND["phase2_protocol"]["read_only_results_wait_max_seconds"]
                    reads = []
                    while time.monotonic() < stop_at:
                        retained_reply = await client.call_tool("interface_results", {
                            "call_id": call_id, "include_image": False})
                        retained_record = record_reply(f"results-{len(reads)}", retained_reply)
                        reads.append(retained_record)
                        retained = retained_record.get("parsed") or {}
                        retained_action = retained.get("action") or {}
                        if retained_action.get("status") in ("completed", "recovered", "failed", "unknown"):
                            dispatch_report = retained
                            action = retained_action
                            break
                        await asyncio.sleep(0.25)
                    outcome["steps"].append({"name": "read_only_results", "polls": reads})
                if action_status not in ("returned", "pending"):
                    raise RuntimeError(f"dispatch envelope status was {action_status!r}")
                if action.get("status") != "completed":
                    raise RuntimeError(f"dispatch action was {action.get('status')!r}")
                result_generation = dispatch_report.get("target_generation") or action.get("target_generation")
                operation_id = dispatch_report.get("operation_id") or action.get("operation_id")
                if result_generation != generation:
                    raise RuntimeError("dispatch generation did not match observation")

                verify_started_ns = time.monotonic_ns()
                verify = await client.call_tool("interface_verify_task", {
                    "call_id": call_id, "wait_for_result_ms": 2000})
                verify_returned_ns = time.monotonic_ns()
                verify_record = record_reply("verify-task", verify)
                verify_record["client_timing_ns"] = {"started": verify_started_ns, "returned": verify_returned_ns}
                outcome["steps"].append({"name": "task_oracle", **verify_record})
                verified = verify_record.get("parsed") or {}
                task_effect = verified.get("task_effect") or {}
                receipt = task_effect.get("receipt") or {}
                if (verify.isError or verified.get("status") != "verified"
                        or verified.get("task_success") is not True
                        or receipt.get("call_id") != call_id
                        or receipt.get("operation_id") != operation_id
                        or receipt.get("target_generation") != generation
                        or receipt.get("oracle_id") != ORACLE_ID):
                    raise RuntimeError("task oracle failed exact action binding or task success")
                actual_effect = json.loads((RUN / "effect.json").read_text(encoding="utf-8"))
                if actual_effect != EXPECTED:
                    raise RuntimeError("fixture side effect did not exactly match frozen expectation")
                close_reply = await client.call_tool("interface_close", {})
                outcome["steps"].append({"name": "server_close", **record_reply("close", close_reply)})
        outcome["status"] = "PASS_SCOPED"
        outcome["call_id"] = call_id
        outcome["operation_id"] = operation_id
        outcome["target_generation"] = generation
    except BaseException as exc:
        outcome["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        if fixture.poll() is None:
            try:
                user32.PostMessageW(ctypes.c_void_p(meta["hwnd"]), 0x0010, 0, 0)
                fixture.wait(timeout=5)
            except Exception:
                fixture.terminate()
                try:
                    fixture.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    fixture.kill()
                    fixture.wait(timeout=3)
        restored = False
        restore_error = None
        if original_foreground and user32.IsWindow(ctypes.c_void_p(original_foreground)):
            restored = bool(user32.SetForegroundWindow(ctypes.c_void_p(original_foreground)))
        current = int(user32.GetForegroundWindow() or 0)
        outcome["cleanup"] = {"fixture_exit_code": fixture.poll(),
            "foreground_restored": bool(restored and current == original_foreground),
            "foreground_before": fg_info(original_foreground) if original_foreground else None,
            "foreground_after": fg_info(current) if current else None,
            "finished_unix_ns": time.time_ns()}
        outcome["ended_monotonic_ns"] = time.monotonic_ns()
        save_json(RUN / "result.json", outcome)

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(main(), timeout=60))
    except BaseException:
        raise


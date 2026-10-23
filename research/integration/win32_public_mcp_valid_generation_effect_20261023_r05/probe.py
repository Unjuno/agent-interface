"""One-shot owned-fixture public-MCP valid-generation effect trial."""
from __future__ import annotations

import asyncio
import base64
import ctypes
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
RAW = PACKET / "raw.json"
CONDITIONS = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
record = {
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": os.environ.get("SOURCE_COMMIT", "UNSET"),
    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "caller_kind": "mcp_stdio",
    "dispatch_attempts": 0,
    "status": "UNKNOWN",
}
children = []
logs = []
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
user32.PostMessageW.restype = ctypes.c_int
user32.IsWindow.argtypes = [ctypes.c_void_p]
user32.IsWindow.restype = ctypes.c_int


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


def parse_response(reply):
    item = next(block for block in reply.content if getattr(block, "type", None) == "text")
    return json.loads(item.text)


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
    record["fixture"] = row
    deadline = time.monotonic() + CONDITIONS["timeouts_seconds"]["fixture_ready"]
    while time.monotonic() < deadline and not meta.exists():
        if process.poll() is not None:
            raise RuntimeError(f"owned fixture exited before ready: {process.returncode}")
        time.sleep(0.025)
    if not meta.exists():
        raise TimeoutError("owned fixture did not become ready within 10 seconds")
    row["meta"] = json.loads(meta.read_text(encoding="utf-8"))
    row["hwnd"] = int(row["meta"]["hwnd"])
    from runtime.backends.win32_v1.backend import Win32Backend
    backend = Win32Backend({"fixture": row["hwnd"]})
    row["target_identity"] = {
        "owner": backend._window_owner_identity_for_hwnd(row["hwnd"]),
        "generation": backend.target_generation("fixture"),
    }
    if row["target_identity"]["owner"]["pid"] != process.pid:
        raise RuntimeError("fixture HWND owner did not match the owned process")
    return process, row


def close_fixture(process, row):
    hwnd = row.get("hwnd")
    row["close_posted"] = bool(hwnd is not None and user32.PostMessageW(hwnd, 0x0010, 0, 0))
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
    row["window_exists_after_exit"] = bool(user32.IsWindow(hwnd)) if hwnd is not None else None
    event_path = Path(row["events_path"])
    row["events"] = ([json.loads(line) for line in event_path.read_text(
        encoding="utf-8").splitlines() if line.strip()] if event_path.exists() else [])
    effect_path = Path(row["effect_path"])
    row["effect"] = json.loads(effect_path.read_text(encoding="utf-8")) if effect_path.exists() else None


async def run_public_calls(targets_path, effect_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets_path),
              "--output-directory", str(RUN / "calls")],
        cwd=str(ROOT))
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await asyncio.wait_for(client.initialize(), 10)
            tools = await asyncio.wait_for(client.list_tools(), 10)
            record["tools"] = sorted(tool.name for tool in tools.tools)
            observed = await asyncio.wait_for(client.call_tool("interface_observe", {
                "target": "fixture", "frame": "window_client", "region": [0, 0, 300, 100]}), 15)
            observe_response = parse_response(observed)
            raw_observation = observe_response.get("receipt", {}).get("source", {}).get("raw_report", {})
            record["public_observation"] = {
                "is_error": observed.isError, "response": observe_response,
                "raw_report": raw_observation, "content": save_content(observed.content)}
            generation = raw_observation.get("target_generation")
            if not isinstance(generation, str):
                raise RuntimeError("public observation did not return target_generation")
            program = {
                "schema": "agent-interface/program-v1",
                "program_id": CONDITIONS["program_id"],
                "source": {"observation_seq": 1, "binding_revision": 1,
                           "target_generations": {"fixture": generation}},
                "authority": {"lease_id": CONDITIONS["program_id"],
                              "expires_at_ns": time.monotonic_ns() + 60_000_000_000},
                "terminal": {"release_all_required": True},
                "ops": CONDITIONS["operations"],
            }
            record["program"] = program
            validated = await asyncio.wait_for(client.call_tool(
                "interface_validate", {"program": program}), 10)
            record["public_validation"] = {
                "is_error": validated.isError, "response": parse_response(validated),
                "content": save_content(validated.content)}
            record["dispatch_attempts"] = 1
            dispatched = await asyncio.wait_for(client.call_tool("interface_dispatch", {
                "program": program, "current_observation_seq": 1,
                "current_binding_revision": 1}), 15)
            body = parse_response(dispatched)
            call_id = body.get("call_id")
            report_path = RUN / "calls" / str(call_id) / "report.json" if call_id else None
            record["public_dispatch"] = {
                "is_error": dispatched.isError, "response": body,
                "content": save_content(dispatched.content),
                "raw_report": json.loads(report_path.read_text(encoding="utf-8"))
                if report_path is not None and report_path.exists() else None}
            deadline = time.monotonic() + CONDITIONS["timeouts_seconds"]["effect_readback"]
            while time.monotonic() < deadline and not effect_path.exists():
                await asyncio.sleep(0.02)
            if effect_path.exists():
                record["effect_readback"] = json.loads(effect_path.read_text(encoding="utf-8"))


def main():
    if sys.platform != "win32":
        raise SystemExit("native Win32 trial requires Windows")
    if record["source_commit"] != CONDITIONS["source_commit"]:
        raise SystemExit("SOURCE_COMMIT does not match frozen conditions")
    text_ops = [op.get("text") for op in CONDITIONS["operations"]
                if isinstance(op, dict) and op.get("op") == "text"]
    if text_ops != [CONDITIONS["text_effect"]]:
        raise SystemExit("frozen text operation does not match frozen expected effect")
    if RUN.exists() or RAW.exists():
        raise SystemExit("one-shot attempt already exists; refusing to overwrite")
    RUN.mkdir(parents=True)
    process = None
    fixture = None
    try:
        process, fixture = start_fixture()
        record["fixture"] = fixture
        targets = RUN / "targets.json"
        targets.write_text(json.dumps({"fixture": fixture["hwnd"]}) + "\n", encoding="utf-8")
        asyncio.run(asyncio.wait_for(run_public_calls(
            targets, Path(fixture["effect_path"])),
            CONDITIONS["timeouts_seconds"]["public_mcp_sequence"]))
        close_fixture(process, fixture)
        dispatch_raw = (record.get("public_dispatch", {}).get("raw_report") or {}).get("result", {})
        effect = record.get("effect_readback")
        record["status"] = (
            "PASS" if record.get("public_observation", {}).get("is_error") is False
            and record.get("public_observation", {}).get("raw_report", {}).get(
                "target_generation_consistency") == "matched"
            and record.get("public_validation", {}).get("response", {}).get("static_valid") is True
            and record.get("dispatch_attempts") == 1
            and dispatch_raw.get("status") == "completed"
            and effect == {"saved": True, "text": CONDITIONS["text_effect"], "clicked": False}
            and fixture.get("effect") == effect
            and fixture.get("exit_code") == 0
            and fixture.get("window_exists_after_exit") is False else "FAIL_OR_UNKNOWN")
    except BaseException as error:
        record["error"] = {"type": type(error).__name__, "detail": str(error)}
        record["status"] = "FAIL_OR_UNKNOWN"
        for owned_process, owned_row in children:
            if owned_process.poll() is not None:
                continue
            try:
                close_fixture(owned_process, owned_row)
            except BaseException as cleanup_error:
                record["cleanup_error"] = {"type": type(cleanup_error).__name__,
                                           "detail": str(cleanup_error)}
    finally:
        record["ended_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        RAW.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        for log in logs:
            log.close()
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

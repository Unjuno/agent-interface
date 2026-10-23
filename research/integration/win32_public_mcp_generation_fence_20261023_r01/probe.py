"""One-shot stale-generation public-MCP check with only an owned-fixture sentinel action."""
from __future__ import annotations

import asyncio
import base64
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

CONDITIONS = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
RAW = ROOT / "raw.json"
RUN = ROOT / "run"
if RAW.exists() or RUN.exists():
    raise SystemExit("frozen result exists; refusing to repeat this trial")
if sys.platform != "win32":
    raise SystemExit("native Win32 trial requires Windows")

record = {
    "schema": "win32-public-mcp-generation-fence-raw-v1",
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": os.environ.get("SOURCE_COMMIT", "UNSET"),
    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "caller_kind": "mcp_stdio",
    "dispatch_attempts": 0,
    "status": "UNKNOWN",
}
children = []
log_handles = []
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL


def target_identity(hwnd):
    backend = Win32Backend({"fixture": int(hwnd)})
    return {"owner": backend._window_owner_identity_for_hwnd(int(hwnd)),
            "generation": backend.target_generation("fixture")}


def start_fixture(label):
    directory = RUN / label
    directory.mkdir(parents=True)
    meta, effect, events = (directory / name for name in
                            ("fixture-meta.json", "effect.json", "events.jsonl"))
    log = (directory / "fixture.log").open("wb")
    log_handles.append(log)
    process = subprocess.Popen(
        [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
         "--meta", str(meta), "--effect", str(effect), "--events", str(events)],
        cwd=str(REPO_ROOT), stdout=log, stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    row = {"label": label, "pid": process.pid, "meta_path": str(meta),
           "effect_path": str(effect), "events_path": str(events),
           "log_path": str(directory / "fixture.log")}
    children.append((process, row))
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and not meta.exists():
        if process.poll() is not None:
            raise RuntimeError(f"owned fixture {label} exited before ready: {process.returncode}")
        time.sleep(0.025)
    if not meta.exists():
        raise TimeoutError(f"owned fixture {label} did not become ready within 10s")
    meta_row = json.loads(meta.read_text(encoding="utf-8"))
    hwnd = int(meta_row["hwnd"])
    row.update(hwnd=hwnd, meta=meta_row, target_identity=target_identity(hwnd))
    if row["target_identity"]["owner"]["pid"] != process.pid:
        raise RuntimeError(f"owned fixture {label} HWND owner does not match process")
    return process, row


def close_fixture(process, row):
    hwnd = row.get("hwnd")
    if hwnd is not None:
        hwnd = int(hwnd)
        posted = bool(user32.PostMessageW(hwnd, 0x0010, 0, 0))
    else:
        posted = False
    row["close_posted"] = posted
    if hwnd is None:
        row["terminate_attempted"] = True
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        row["terminate_attempted"] = True
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            row["kill_attempted"] = True
            process.kill()
            process.wait(timeout=2)
    row["exit_code"] = process.returncode
    row["window_exists_after_exit"] = bool(user32.IsWindow(hwnd)) if hwnd is not None else None
    if Path(row["events_path"]).exists():
        row["events"] = [json.loads(line) for line in Path(row["events_path"]).read_text(
            encoding="utf-8").splitlines() if line.strip()]
    else:
        row["events"] = []
    row["effect_exists"] = Path(row["effect_path"]).exists()


def save_content(blocks):
    result = []
    for block in blocks:
        kind = getattr(block, "type", None)
        if kind == "text":
            result.append({"type": "text", "text": block.text})
        elif kind == "image":
            data = block.data
            result.append({"type": "image", "mimeType": block.mimeType,
                           "data_b64": data if isinstance(data, str)
                           else base64.b64encode(data).decode("ascii")})
        else:
            result.append({"type": str(kind), "repr": repr(block)})
    return result


def parse_response(reply):
    block = next(item for item in reply.content if getattr(item, "type", None) == "text")
    return json.loads(block.text)


async def public_observe(targets_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets_path),
              "--output-directory", str(RUN / "calls-a")], cwd=str(REPO_ROOT))
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await asyncio.wait_for(client.initialize(), 10)
            listed = await asyncio.wait_for(client.list_tools(), 10)
            record["tools_a"] = sorted(tool.name for tool in listed.tools)
            reply = await asyncio.wait_for(client.call_tool("interface_observe", {
                "target": "fixture", "frame": "window_client", "region": [0, 0, 300, 100]}), 15)
            body = parse_response(reply)
            raw_report = body.get("receipt", {}).get("source", {}).get("raw_report", {})
            record["public_observation"] = {"is_error": reply.isError,
                "response": body, "raw_report": raw_report,
                "content": save_content(reply.content)}


async def public_validate_and_dispatch(targets_path, old_generation):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets_path),
              "--output-directory", str(RUN / "calls-b")], cwd=str(REPO_ROOT))
    program = {
        "schema": "agent-interface/program-v1",
        "program_id": "generation-fence-r01-stale-target",
        "source": {"observation_seq": 1, "binding_revision": 1,
                   "target_generations": {"fixture": old_generation}},
        "authority": {"lease_id": "generation-fence-r01",
                      "expires_at_ns": time.monotonic_ns() + 60_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": [{"op": "focus", "target": "fixture"},
                {"op": "text", "text": "STALE-GENERATION-MUST-NOT-BE-TYPED"},
                {"op": "release_all"}],
    }
    record["program"] = program
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await asyncio.wait_for(client.initialize(), 10)
            listed = await asyncio.wait_for(client.list_tools(), 10)
            record["tools_b"] = sorted(tool.name for tool in listed.tools)
            valid_reply = await asyncio.wait_for(client.call_tool("interface_validate",
                {"program": program}), 10)
            record["public_validation"] = {"is_error": valid_reply.isError,
                "content": save_content(valid_reply.content),
                "report": parse_response(valid_reply)}
            record["dispatch_attempts"] = 1
            dispatch_reply = await asyncio.wait_for(client.call_tool("interface_dispatch", {
                "program": program, "current_observation_seq": 1,
                "current_binding_revision": 1}), 15)
            body = parse_response(dispatch_reply)
            call_id = body.get("call_id")
            call_report = None
            if isinstance(call_id, str):
                path = RUN / "calls-b" / call_id / "report.json"
                if path.exists():
                    call_report = json.loads(path.read_text(encoding="utf-8"))
            record["public_dispatch"] = {"is_error": dispatch_reply.isError,
                "response": body, "content": save_content(dispatch_reply.content),
                "raw_report": call_report}


def main():
    RUN.mkdir(parents=True)
    old_process = new_process = None
    old = new = None
    try:
        if record["source_commit"] != CONDITIONS["source_commit"]:
            raise ValueError("SOURCE_COMMIT does not match frozen conditions")
        old_process, old = start_fixture("fixture-a")
        old_targets = RUN / "targets-a.json"
        old_targets.write_text(json.dumps({"fixture": old["hwnd"]}) + "\n", encoding="utf-8")
        asyncio.run(asyncio.wait_for(public_observe(old_targets), timeout=45))
        observed_generation = record["public_observation"].get("raw_report", {}).get("target_generation")
        if observed_generation != old["target_identity"]["generation"]:
            raise RuntimeError("public observation did not expose the owned target generation")
        close_fixture(old_process, old)
        new_process, new = start_fixture("fixture-b")
        new_targets = RUN / "targets-b.json"
        new_targets.write_text(json.dumps({"fixture": new["hwnd"]}) + "\n", encoding="utf-8")
        if new["target_identity"]["generation"] == observed_generation:
            raise RuntimeError("new owned process did not yield a distinct target generation")
        asyncio.run(asyncio.wait_for(
            public_validate_and_dispatch(new_targets, observed_generation), timeout=50))
        close_fixture(new_process, new)
        record["fixture_a"] = old
        record["fixture_b"] = new
        dispatch_result = record.get("public_dispatch", {}).get("raw_report", {}).get("result", {})
        record["status"] = (
            "PASS" if record.get("public_observation", {}).get("is_error") is False
            and record.get("public_validation", {}).get("report", {}).get("static_valid") is True
            and dispatch_result.get("status") == "refused"
            and dispatch_result.get("error") == "TARGET_GENERATION_CHANGED"
            and dispatch_result.get("input_dispatched") is False
            and [item.get("kind") for item in new.get("events", [])] == ["ready"]
            and not new.get("effect_exists") else "FAIL_OR_UNKNOWN")
    except BaseException as error:
        record["status"] = "UNKNOWN"
        record["error_type"] = type(error).__name__
        record["error"] = str(error)
    finally:
        for process, fixture in children:
            if process is not None and fixture is not None and process.poll() is None:
                try:
                    close_fixture(process, fixture)
                except BaseException as error:
                    fixture["cleanup_error"] = repr(error)
        fixtures_by_label = {fixture.get("label"): fixture for _, fixture in children}
        if old is not None:
            fixtures_by_label.setdefault("fixture-a", old)
        if new is not None:
            fixtures_by_label.setdefault("fixture-b", new)
        if "fixture-a" in fixtures_by_label:
            record["fixture_a"] = fixtures_by_label["fixture-a"]
        if "fixture-b" in fixtures_by_label:
            record["fixture_b"] = fixtures_by_label["fixture-b"]
            record["fixture_b_events"] = fixtures_by_label["fixture-b"].get("events", [])
            record["fixture_b_effect_exists"] = fixtures_by_label["fixture-b"].get("effect_exists")
        record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        for handle in log_handles:
            handle.close()
        RAW.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    if record["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

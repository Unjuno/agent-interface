import asyncio
import base64
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


DISPLAY = ":142"
OUT = Path("/evidence/formal01")
SOURCE_COMMIT = os.environ["SOURCE_COMMIT"]
IMAGE_ID = os.environ["EXPERIMENT_IMAGE_ID"]
ENV = dict(os.environ, DISPLAY=DISPLAY)
APPS = [
    ("inkscape", ["inkscape"], "inkscape"),
    ("calc", ["libreoffice", "--calc"], "libreoffice-calc"),
    ("chromium", ["chromium", "--no-sandbox", "--disable-gpu",
                   "--disable-dev-shm-usage", "--user-data-dir=/tmp/chromium-formal01",
                   "about:blank"], "chromium"),
]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode()
    path.write_bytes(data + b"\n")
    return hashlib.sha256(data + b"\n").hexdigest()


def read_processes():
    rows = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "stat").read_text()
            tail = raw[raw.rfind(")") + 2:].split()
            rows[int(entry.name)] = {"ppid": int(tail[1]), "state": tail[0]}
        except (OSError, ValueError, IndexError):
            pass
    return rows


def descendants(root):
    tree = read_processes()
    found = {root}
    changed = True
    while changed:
        changed = False
        for pid, row in tree.items():
            if row["ppid"] in found and pid not in found:
                found.add(pid)
                changed = True
    return found


def visible_windows():
    q = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", ".*"],
                       env=ENV, text=True, capture_output=True, check=False)
    return {int(x) for x in q.stdout.splitlines() if x.strip().isdigit()}


def inspect_window(wid):
    prop = subprocess.run(["xprop", "-id", str(wid), "_NET_WM_PID", "WM_CLASS", "WM_NAME"],
                          env=ENV, text=True, capture_output=True, check=False)
    geo = subprocess.run(["xdotool", "getwindowgeometry", str(wid)],
                         env=ENV, text=True, capture_output=True, check=False)
    owner = re.search(r"_NET_WM_PID\(CARDINAL\) = (\d+)", prop.stdout)
    size = re.search(r"Geometry: (\d+)x(\d+)", geo.stdout)
    return {"window_id": wid, "properties": prop.stdout, "geometry_text": geo.stdout,
            "owner_pid": int(owner.group(1)) if owner else None,
            "size": [int(size.group(1)), int(size.group(2))] if size else None}


def launch_owned(name, argv, class_hint):
    before = visible_windows()
    proc = subprocess.Popen(argv, env=ENV, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
    deadline = time.monotonic() + 45
    candidates = []
    while time.monotonic() < deadline:
        process_tree = descendants(proc.pid)
        for wid in sorted(visible_windows() - before):
            row = inspect_window(wid)
            candidates.append(row)
            if (row["owner_pid"] in process_tree and row["size"] and
                    min(row["size"]) >= 100 and class_hint in row["properties"].lower()):
                return proc, {"name": name, "launcher_pid": proc.pid,
                              "owned_pids_at_binding": sorted(process_tree), **row}
        time.sleep(.25)
    raise RuntimeError(f"{name}: no new visible class/owner-bound surface; candidates={candidates[-12:]}")


def text_payload(result):
    texts = [item.text for item in result.content if getattr(item, "type", None) == "text"]
    if not texts:
        raise AssertionError("MCP response omitted text receipt")
    return json.loads(texts[0])


def save_mcp_response(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = result.model_dump(mode="json")
    data = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False).encode()
    path.write_bytes(data + b"\n")
    blocks = []
    for item in result.content:
        row = {"type": getattr(item, "type", None)}
        if getattr(item, "type", None) == "image":
            raw = base64.b64decode(item.data, validate=True)
            image_path = path.parent / "images" / (path.stem + ".png")
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(raw)
            row.update(mimeType=item.mimeType, byte_length=len(raw),
                       sha256=hashlib.sha256(raw).hexdigest(), path=str(image_path))
        elif getattr(item, "type", None) == "text":
            row.update(text_sha256=hashlib.sha256(item.text.encode()).hexdigest())
        blocks.append(row)
    return {"response_sha256": hashlib.sha256(data + b"\n").hexdigest(), "blocks": blocks}


def server_processes():
    result = []
    for pid in read_processes():
        try:
            argv = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        if "runtime.cli_v1.mcp_server" in argv:
            result.append({"pid": pid, "argv": argv.strip()})
    return result


async def mcp_sequence(targets):
    params = StdioServerParameters(command="python3", args=[
        "-m", "runtime.cli_v1.mcp_server", "--targets", str(OUT / "targets.json"),
        "--output-directory", str(OUT / "server-receipts"), "--display", DISPLAY,
        "--session-mode", "persistent-x11"], env=ENV, cwd="/opt/importroot")
    trace = {"requested_order": ["inkscape", "calc", "chromium", "close"],
             "calls": [], "retained_reads_after_close": []}
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init = await session.initialize()
            listing = await session.list_tools()
            names = sorted(tool.name for tool in listing.tools)
            trace["initialize_protocol_version"] = init.protocolVersion
            trace["tool_names"] = names
            expected = {"interface_observe", "interface_results", "interface_close", "interface_dispatch"}
            if not expected.issubset(names):
                raise AssertionError(f"public MCP tools missing: {sorted(expected - set(names))}")
            trace["server_processes_during_session"] = server_processes()
            for index, name in enumerate(("inkscape", "calc", "chromium"), start=1):
                result = await session.call_tool("interface_observe", {
                    "target": name, "frame": "window_client", "region": [0, 0, 128, 96]})
                raw_path = OUT / "mcp-responses" / f"{index:02d}-observe-{name}.json"
                evidence = save_mcp_response(raw_path, result)
                payload = text_payload(result)
                if result.isError or payload.get("status") != "returned":
                    raise AssertionError(f"{name} observation did not return: {payload}")
                if payload.get("input_dispatched") is not False or payload.get("side_effect_authority") is not False:
                    raise AssertionError(f"{name} observation carried authority/input: {payload}")
                if not any(getattr(item, "type", None) == "image" for item in result.content):
                    raise AssertionError(f"{name} response omitted image block")
                session_row = payload.get("session")
                if not isinstance(session_row, dict) or session_row.get("state") != "open":
                    raise AssertionError(f"{name} response omitted open session identity")
                record = {"target": name, "response_file": str(raw_path), **evidence,
                          "call_id": payload.get("call_id"),
                          "call_directory": payload.get("call_directory"),
                          "session": session_row,
                          "observation_id": payload.get("observation", {}).get("observation_id"),
                          "observation_status": payload.get("observation", {}).get("status")}
                trace["calls"].append(record)
            session_ids = {row["session"].get("session_id") for row in trace["calls"]}
            if len(session_ids) != 1 or None in session_ids:
                raise AssertionError(f"observation session IDs diverged: {session_ids}")
            trace["session_id"] = next(iter(session_ids))
            close_result = await session.call_tool("interface_close", {})
            close_path = OUT / "mcp-responses" / "04-close.json"
            close_evidence = save_mcp_response(close_path, close_result)
            close_payload = text_payload(close_result)
            if close_result.isError or close_payload.get("status") != "closed":
                raise AssertionError(f"close did not return neutral closed: {close_payload}")
            close_row = {"response_file": str(close_path), **close_evidence,
                         "call_id": close_payload.get("call_id"),
                         "call_directory": close_payload.get("call_directory"),
                         "session": close_payload.get("session"),
                         "close_report": close_payload}
            trace["close"] = close_row
            if close_row["session"].get("session_id") != trace["session_id"]:
                raise AssertionError("close session ID mismatch")
            if close_payload.get("release_attempted") is not False or close_payload.get("connection_close_attempted") is not True:
                raise AssertionError(f"close did not report observation-only neutral cleanup: {close_payload}")
            for call in [*trace["calls"], close_row]:
                result = await session.call_tool("interface_results", {
                    "call_id": call["call_id"], "include_image": False})
                path = OUT / "mcp-responses" / f"retained-{call['call_id']}.json"
                evidence = save_mcp_response(path, result)
                payload = text_payload(result)
                if result.isError or payload.get("retained_call", {}).get("state") != "finished":
                    raise AssertionError(f"post-close result not retained: {payload}")
                if payload.get("operation_invoked") is not False:
                    raise AssertionError("interface_results invoked an operation")
                trace["retained_reads_after_close"].append({"call_id": call["call_id"],
                    "status": payload.get("status"), "session_id": payload.get("session", {}).get("session_id"),
                    "response_file": str(path), **evidence})
            trace["server_processes_after_close_before_client_exit"] = server_processes()
    trace["server_processes_after_transport_shutdown"] = server_processes()
    return trace


def terminate_tree(root):
    owned = descendants(root)
    states = read_processes()
    for pid in sorted(owned, reverse=True):
        row = states.get(pid)
        if row and row["state"] != "Z":
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except PermissionError:
                pass
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        states = read_processes()
        live = [pid for pid in owned if pid in states and states[pid]["state"] != "Z"]
        if not live:
            break
        time.sleep(.05)
    states = read_processes()
    live = [pid for pid in owned if pid in states and states[pid]["state"] != "Z"]
    return {"owned_pids": sorted(owned), "still_running_pids": sorted(live),
            "zombie_pids": sorted(pid for pid in owned if pid in states and states[pid]["state"] == "Z")}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    for name in ("mcp-responses", "server-receipts"):
        (OUT / name).mkdir()
    environment = {"source_commit": SOURCE_COMMIT, "image_id": IMAGE_ID,
                   "base_image_id": "sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3",
                   "platform": "linux/amd64", "display": DISPLAY}
    write_json(OUT / "environment.json", environment)
    display = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launched = [display]
    rows = []
    outcome = {"decision": "STOP_PUBLIC_MCP_THREE_APP", "input_operations": 0,
               "model_calls": 0, "network_calls": 0, "authority_granted": False}
    try:
        for _ in range(100):
            if Path("/tmp/.X11-unix/X142").exists():
                break
            time.sleep(.05)
        if not Path("/tmp/.X11-unix/X142").exists():
            raise RuntimeError("Xvfb socket not ready")
        wm = subprocess.Popen(["openbox", "--replace"], env=ENV,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        launched.append(wm)
        time.sleep(.6)
        targets = {}
        for name, argv, class_hint in APPS:
            proc, identity = launch_owned(name, argv, class_hint)
            launched.append(proc)
            rows.append(identity)
            targets[name] = identity["window_id"]
        if len(set(targets.values())) != 3:
            raise AssertionError("three targets did not resolve to distinct native windows")
        write_json(OUT / "app-identities.json", rows)
        write_json(OUT / "targets.json", targets)
        mcp = asyncio.run(mcp_sequence(targets))
        write_json(OUT / "mcp-trace.json", mcp)
        outcome.update(decision="PASS_PUBLIC_MCP_THREE_APP_OBSERVE_CLOSE_SCOPED",
                       session_id=mcp["session_id"], observation_count=len(mcp["calls"]),
                       close=mcp["close"]["close_report"],
                       retained_read_count=len(mcp["retained_reads_after_close"]))
    except Exception as error:
        outcome.update(decision="FAIL_PUBLIC_MCP_THREE_APP" if rows else "STOP_PUBLIC_MCP_THREE_APP",
                       error=repr(error))
    finally:
        stopped = []
        for proc in reversed(launched):
            stopped.append({"pid": proc.pid, **terminate_tree(proc.pid)})
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
        outcome["app_process_cleanup"] = stopped
        outcome["owned_mcp_server_processes_after_transport_shutdown"] = server_processes()
        outcome["remaining_running_owned_pids"] = sorted({
            pid for item in stopped for pid in item["still_running_pids"]})
        outcome["x_socket_absent_after_cleanup"] = not Path("/tmp/.X11-unix/X142").exists()
        outcome["app_identities"] = rows
        write_json(OUT / "result.json", outcome)
    print(json.dumps(outcome, sort_keys=True))
    return 0 if outcome["decision"] == "PASS_PUBLIC_MCP_THREE_APP_OBSERVE_CLOSE_SCOPED" and not outcome["remaining_running_owned_pids"] and not outcome["owned_mcp_server_processes_after_transport_shutdown"] and outcome["x_socket_absent_after_cleanup"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

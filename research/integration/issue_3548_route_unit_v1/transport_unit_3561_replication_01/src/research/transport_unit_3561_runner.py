#!/usr/bin/env python3
"""One observation through direct API, CLI, and public stdio MCP."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import timedelta

sys.path.insert(0, "/src")
from Xlib import display

ROOT = Path("/evidence")
DISPLAY = ":219"
TITLE = "route-unit-3561"
MESSAGE = "Agent Interface route fixture v1"
REGION = [0, 0, 500, 260]
ENV = {**os.environ, "DISPLAY": DISPLAY, "PYTHONPATH": "/src",
       "PYTHONDONTWRITEBYTECODE": "1"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def locate_window():
    d = display.Display(DISPLAY)
    try:
        matches = []
        for w in d.screen().root.query_tree().children:
            try:
                title = w.get_wm_name()
                geo = w.get_geometry()
                if title == TITLE:
                    matches.append({"xid": int(w.id), "title": title,
                                    "width": int(geo.width), "height": int(geo.height)})
            except Exception:
                continue
        if len(matches) != 1:
            raise RuntimeError(f"FIXTURE_WINDOW_COUNT:{len(matches)}")
        row = matches[0]
        if [row["width"], row["height"]] != [500, 260]:
            raise RuntimeError(f"FIXTURE_GEOMETRY:{row}")
        return row
    finally:
        d.close()


def start_fixture():
    proc = subprocess.Popen(
        ["xmessage", "-name", TITLE, "-title", TITLE,
         "-geometry", "500x260+20+20", MESSAGE],
        env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out, err = proc.communicate()
            raise RuntimeError("FIXTURE_EXITED:" + err.decode("utf-8", "replace"))
        try:
            meta = locate_window()
            return proc, meta
        except Exception:
            time.sleep(.025)
    proc.terminate()
    out, err = proc.communicate(timeout=3)
    raise RuntimeError("FIXTURE_WINDOW_TIMEOUT:" + err.decode("utf-8", "replace"))


def call_mcp(target_file, receipt_dir):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        params = StdioServerParameters(
            command="python3",
            args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(target_file),
                  "--output-directory", str(receipt_dir), "--display", DISPLAY],
            env=ENV, cwd="/src")
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                initialized = await session.initialize()
                listed = await session.list_tools()
                result = await session.call_tool(
                    "interface_observe",
                    {"target": "fixture", "frame": "window_client",
                     "region": REGION, "compact": False},
                    read_timeout_seconds=timedelta(seconds=20))
                text_block = next((x.text for x in result.content
                                   if getattr(x, "type", None) == "text"), None)
                image_block = next((x for x in result.content
                                    if getattr(x, "type", None) == "image"), None)
                metadata = json.loads(text_block) if text_block else {}
                png = base64.b64decode(image_block.data) if image_block else b""
                active_pids = scan_mcp_server_pids()
                reply = {
                    "initialized": initialized.model_dump(mode="json"),
                    "tool_names": [tool.name for tool in listed.tools],
                    "is_error": result.isError,
                    "metadata": metadata,
                    "image_mime_type": image_block.mimeType if image_block else None,
                    "image_png": png,
                    "server_pids_during_call": active_pids,
                }
        reply["server_pids_after_close"] = scan_mcp_server_pids()
        return reply
    return asyncio.run(run())


def scan_mcp_server_pids():
    found = []
    for path in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            argv = path.read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
            if "runtime.cli_v1.mcp_server" in argv:
                found.append(int(path.parent.name))
        except (OSError, ValueError):
            continue
    return sorted(found)


def wait_child(proc, route):
    if proc.poll() is None:
        proc.terminate()
    try:
        out, err = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    return {"route": route, "pid": proc.pid, "exit_code": proc.returncode,
            "reaped": proc.poll() is not None,
            "stdout": out.decode("utf-8", "replace"),
            "stderr": err.decode("utf-8", "replace")}


def observation_from_api(row):
    return row.get("observation", {}) if isinstance(row, dict) else {}


def observe_once(route, target_path, window, image_dir, fixture_proc):
    target_id = window["xid"]
    targets = {"fixture": target_id}
    target_path.write_text(json.dumps(targets, sort_keys=True) + "\n")
    image_dir.mkdir()
    started = time.monotonic_ns()
    if route == "api":
        from runtime.cli_v1.observe import observe
        result = observe(targets, target="fixture", frame="window_client",
                         region=REGION, capture_directory=str(image_dir),
                         display_name=DISPLAY)
        elapsed = time.monotonic_ns() - started
        observation = observation_from_api(result)
        artifact = observation.get("artifact", {})
        png_path = Path(artifact.get("path", ""))
        png = png_path.read_bytes() if png_path.is_file() else b""
        pixel_sha = observation.get("sha256")
        status = result.get("status")
        return_code = 0 if status == "returned" else 2
        text_result = result
        capture = observation
    elif route == "cli":
        proc = subprocess.run(
            ["python3", "-m", "runtime.cli_v1", "observe",
             "--targets", str(target_path), "--target", "fixture",
             "--frame", "window_client", "--region", *(str(x) for x in REGION),
             "--capture-directory", str(image_dir), "--display", DISPLAY],
            env=ENV, capture_output=True, timeout=20)
        elapsed = time.monotonic_ns() - started
        text_result = json.loads(proc.stdout.decode("utf-8"))
        text_result["_stderr"] = proc.stderr.decode("utf-8", "replace")
        return_code = proc.returncode
        observation = observation_from_api(text_result)
        artifact = observation.get("artifact", {})
        png_path = Path(artifact.get("path", ""))
        png = png_path.read_bytes() if png_path.is_file() else b""
        pixel_sha = observation.get("sha256")
        status = text_result.get("status")
        capture = observation
    else:
        mcp_result = call_mcp(target_path, ROOT/"mcp-receipts")
        elapsed = time.monotonic_ns() - started
        text_result = {k: v for k, v in mcp_result.items() if k != "image_png"}
        png = mcp_result["image_png"]
        metadata = mcp_result["metadata"]
        receipt = metadata.get("receipt", {})
        raw = receipt.get("source", {}).get("raw_report", {}) if isinstance(receipt, dict) else {}
        observation = observation_from_api(raw)
        pixel_sha = observation.get("sha256")
        capture = metadata.get("image_reference", {}).get("recorded_capture", {})
        status = raw.get("status")
        return_code = 0 if not mcp_result["is_error"] else 2
    png_path = ROOT/f"{route}.png"
    if png:
        png_path.write_bytes(png)
    row = {
        "route": route, "status": status, "return_code": return_code,
        "request": {"operation": "observe", "target_name": "fixture",
                    "native_target_id": target_id, "frame": "window_client",
                    "region": REGION},
        "fixture_window": window, "fixture_process_pid": fixture_proc.pid,
        "capture": capture, "raw_result": text_result,
        "elapsed_ns": elapsed, "raw_pixel_sha256": pixel_sha,
        "png_path": str(png_path), "png_sha256": digest(png) if png else None,
        "png_bytes": len(png), "input_dispatched": False,
    }
    (ROOT/f"{route}.json").write_text(json.dumps(row, indent=2, sort_keys=True)+"\n")
    return row


def main():
    if ROOT.exists():
        if any(ROOT.iterdir()):
            raise RuntimeError("OUTPUT_DIRECTORY_NOT_EMPTY")
    else:
        ROOT.mkdir(parents=True, exist_ok=False)
    rows, children = [], []
    xvfb = None
    failure = None
    try:
        xvfb = subprocess.Popen(
            ["/usr/bin/Xvfb", DISPLAY, "-screen", "0", "640x480x24", "-nolisten", "tcp"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(.25)
        if xvfb.poll() is not None:
            out, err = xvfb.communicate()
            raise RuntimeError("XVFB_EXITED:" + err.decode("utf-8", "replace"))
        for route in ("api", "cli", "mcp"):
            attempt = {"route": route, "attempt_count": 1, "observation_count": 0}
            fixture = None
            try:
                fixture, window = start_fixture()
                attempt["fixture_window"] = window
                row = observe_once(route, ROOT/"targets.json", window,
                                   ROOT/f"{route}-images", fixture)
                attempt["observation_count"] = 1
                rows.append(row)
                attempt["observation"] = row
            except Exception as error:
                attempt["error"] = repr(error)
                failure = {"route": route, "error": repr(error)}
                raise
            finally:
                if fixture is not None:
                    attempt["fixture_cleanup"] = wait_child(fixture, route)
                (ROOT/f"{route}-attempt.json").write_text(
                    json.dumps(attempt, indent=2, sort_keys=True)+"\n")
        decision = "HOLD_PENDING_INDEPENDENT_AUDIT"
    except Exception as error:
        failure = failure or {"route": "runner", "error": repr(error)}
        decision = "STOP_ROUTE_UNAVAILABLE" if rows else "STOP_RUNNER_INFRA"
    finally:
        if xvfb is not None:
            if xvfb.poll() is None:
                xvfb.terminate()
            try:
                out, err = xvfb.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                out, err = xvfb.communicate()
            xvfb_cleanup = {"pid": xvfb.pid, "exit_code": xvfb.returncode,
                            "reaped": xvfb.poll() is not None,
                            "stderr": err.decode("utf-8", "replace")}
        else:
            xvfb_cleanup = {"started": False}
    summary = {
        "schema": "transport-unit-3561-v1", "decision": decision,
        "route_count": len(rows), "routes": [r["route"] for r in rows],
        "network": "none", "input_dispatched": False,
        "failure": failure, "xvfb_cleanup": xvfb_cleanup,
    }
    if len(rows) == 3:
        summary["raw_pixel_sha256_equal"] = (
            all(r["raw_pixel_sha256"] for r in rows) and
            len({r["raw_pixel_sha256"] for r in rows}) == 1)
    (ROOT/"summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n")
    (ROOT/"cleanup.json").write_text(json.dumps({
        "xvfb": xvfb_cleanup,
        "fixtures": [row.get("fixture_process_pid") for row in rows],
        "fixture_attempts": [row for row in rows],
    }, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"decision": decision, "route_count": len(rows),
                      "routes": summary["routes"], "failure": failure}, sort_keys=True))
    if failure:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

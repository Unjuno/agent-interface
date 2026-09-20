"""One no-input X11 observation through public API, CLI, and stdio MCP."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path("/repo")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from runtime.cli_v1.observe import observe
from runtime.cli_v1.review import present_result


EVIDENCE = Path(os.environ["AI3548_EVIDENCE"]).resolve()
TARGET_NAME = "fixture"
FRAME = "window_client"
REGION = [0, 0, 500, 260]
MESSAGE = "ISSUE 3548\nSame read-only observation target\nNo input is sent."


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wait_for_window(proc: subprocess.Popen, timeout: float = 8.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"fixture exited early: {proc.returncode}")
        result = subprocess.run(["xwininfo", "-name", "AI3548 fixed observation fixture"],
                                capture_output=True, text=True, check=False)
        match = re.search(r"Window id:\s+(0x[0-9a-fA-F]+)", result.stdout)
        if match:
            return int(match.group(1), 16)
        time.sleep(0.05)
    raise TimeoutError("fixture window did not appear")


def launch_fixture(route_dir: Path):
    proc = subprocess.Popen(["xmessage", "-name", "AI3548Fixture", "-title",
        "AI3548 fixed observation fixture", "-geometry", "500x260+20+20",
        "-bg", "#d0e0f0", "-fg", "#102030", "-fn", "fixed", "-buttons", "",
        MESSAGE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    xid = wait_for_window(proc)
    (route_dir / "target.json").write_text(
        json.dumps({TARGET_NAME: xid}, sort_keys=True) + "\n", encoding="utf-8")
    return proc, xid


def stop_fixture(proc: subprocess.Popen) -> dict:
    proc.terminate()
    try:
        stdout, stderr = proc.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=3)
    return {"exit_code": proc.returncode, "stdout": stdout, "stderr": stderr}


def persist_envelope(route_dir: Path, envelope: dict, start_ns: int, end_ns: int,
                     process_record: dict) -> dict:
    raw = json.dumps(envelope, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    (route_dir / "envelope.json").write_bytes(raw)
    image = envelope.get("image")
    if not isinstance(image, dict) or image.get("mimeType") != "image/png":
        raise RuntimeError("route did not return one PNG image block")
    png = base64.b64decode(image["data"], validate=True)
    (route_dir / "image.png").write_bytes(png)
    from PIL import Image
    import io
    with Image.open(io.BytesIO(png)) as opened:
        rgb = opened.convert("RGB")
        pixels = rgb.tobytes()
        dimensions = list(rgb.size)
    receipt_source = envelope.get("receipt", {}).get("source", {})
    raw_report = receipt_source.get("raw_report", {})
    observation = raw_report.get("observation", {})
    if raw_report.get("status") != "returned" or not isinstance(observation.get("sha256"), str):
        raise RuntimeError(f"observation did not return captured data: {raw_report}")
    info = {"route": route_dir.name, "request": {"target": TARGET_NAME,
        "native_window_id": process_record["native_window_id"], "frame": FRAME,
        "region": REGION}, "observation": {"target": observation.get("target"),
        "native_window_id": observation.get("native_window_id"),
        "frame": observation.get("frame"), "region": observation.get("region"),
        "width": observation.get("width"), "height": observation.get("height"),
        "raw_pixel_sha256": observation.get("sha256"),
        "artifact_source_raw_sha256": observation.get("artifact", {}).get("source_raw_sha256")},
        "status": envelope.get("outcome_summary", {}).get("reported_status",
        envelope.get("status")), "image_status": envelope.get("image_status", "image"),
        "side_effect_authority": raw_report.get("side_effect_authority"),
        "input_dispatched": raw_report.get("input_dispatched"),
        "mime_type": "image/png", "png_sha256": sha(png), "pixel_sha256": sha(pixels),
        "dimensions": dimensions, "elapsed_ns": end_ns - start_ns,
        "call_started_monotonic_ns": start_ns, "call_ended_monotonic_ns": end_ns,
        "attempt_count": 1, "process": process_record}
    write_json(route_dir / "route.json", info)
    return info


def run_api(route_dir: Path) -> dict:
    route_dir.mkdir(parents=True)
    fixture, xid = launch_fixture(route_dir)
    try:
        target_map = {TARGET_NAME: xid}
        t0 = time.monotonic_ns()
        report = observe(target_map, target=TARGET_NAME, frame=FRAME, region=REGION,
                         capture_directory=str(route_dir / "captures"))
        envelope = present_result(report, route_dir)
        t1 = time.monotonic_ns()
        write_json(route_dir / "report.json", report)
        return persist_envelope(route_dir, envelope, t0, t1,
            {"kind": "in_process_public_python_api", "pid": os.getpid(),
             "fixture": stop_fixture(fixture), "native_window_id": xid})
    finally:
        if fixture.poll() is None:
            stop_fixture(fixture)


def run_cli(route_dir: Path) -> dict:
    route_dir.mkdir(parents=True)
    fixture, xid = launch_fixture(route_dir)
    try:
        target_path = route_dir / "target.json"
        capture_dir = route_dir / "captures"
        command = [sys.executable, "-m", "runtime.cli_v1", "observe", "--targets",
            str(target_path), "--target", TARGET_NAME, "--frame", FRAME,
            "--region", *map(str, REGION), "--capture-directory", str(capture_dir), "--review"]
        t0 = time.monotonic_ns()
        child = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
        try:
            stdout, stderr = child.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            child.kill()
            stdout, stderr = child.communicate(timeout=3)
            raise TimeoutError(f"CLI route timed out; pid={child.pid}")
        t1 = time.monotonic_ns()
        (route_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
        (route_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
        (route_dir / "command.json").write_text(json.dumps(command) + "\n", encoding="utf-8")
        (route_dir / "exit-code.txt").write_text(f"{child.returncode}\n", encoding="ascii")
        if child.returncode != 0:
            raise RuntimeError(f"CLI exit {child.returncode}: {stderr}")
        envelope = json.loads(stdout)
        write_json(route_dir / "report.json",
                   envelope.get("receipt", {}).get("source", {}).get("raw_report"))
        return persist_envelope(route_dir, envelope, t0, t1,
            {"kind": "cli_subprocess", "pid": child.pid, "exit_code": child.returncode,
             "fixture": stop_fixture(fixture), "native_window_id": xid})
    finally:
        if fixture.poll() is None:
            stop_fixture(fixture)


async def run_mcp_async(route_dir: Path) -> dict:
    route_dir.mkdir(parents=True)
    fixture, xid = launch_fixture(route_dir)
    try:
        target_path = route_dir / "target.json"
        params = StdioServerParameters(command=sys.executable, args=["-m",
            "runtime.cli_v1.mcp_server", "--targets", str(target_path),
            "--output-directory", str(route_dir / "calls"), "--display", ":99"])
        t0 = time.monotonic_ns()
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                tools = await client.list_tools()
                listed = sorted(tool.name for tool in tools.tools)
                if "interface_observe" not in listed:
                    raise RuntimeError(f"observe tool unavailable: {listed}")
                reply = await client.call_tool("interface_observe", {
                    "target": TARGET_NAME, "frame": FRAME, "region": REGION})
        t1 = time.monotonic_ns()
        blocks = []
        envelope = None
        image = None
        for block in reply.content:
            if getattr(block, "type", None) == "text":
                blocks.append({"type": "text", "text": block.text})
                envelope = json.loads(block.text)
            elif getattr(block, "type", None) == "image":
                image = {"mimeType": block.mimeType, "data": block.data}
                blocks.append({"type": "image", "mimeType": block.mimeType,
                               "data_sha256": sha(base64.b64decode(block.data))})
        if envelope is None or image is None:
            raise RuntimeError("MCP did not return text metadata and a separate image block")
        envelope["image"] = image
        write_json(route_dir / "mcp-blocks.json", blocks)
        write_json(route_dir / "mcp-tool-names.json", listed)
        return persist_envelope(route_dir, envelope, t0, t1,
            {"kind": "stdio_mcp_subprocess", "pid": None, "tool_names": listed,
             "fixture": stop_fixture(fixture), "native_window_id": xid})
    finally:
        if fixture.poll() is None:
            stop_fixture(fixture)


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=False)
    display = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x800x24",
        "-nolisten", "tcp", "-ac"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    openbox = None
    try:
        os.environ["DISPLAY"] = ":99"
        for _ in range(100):
            if display.poll() is not None:
                raise RuntimeError("Xvfb exited")
            if subprocess.run(["xdpyinfo"], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0:
                break
            time.sleep(0.05)
        else:
            raise TimeoutError("Xvfb did not become ready")
        openbox = subprocess.Popen(["openbox"], stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        time.sleep(0.25)
        rows = [run_api(EVIDENCE / "api"), run_cli(EVIDENCE / "cli"),
                asyncio.run(run_mcp_async(EVIDENCE / "mcp"))]
        write_json(EVIDENCE / "comparison.json", rows)
        source_paths = ["research/integration/issue_3548_route_unit_v1/route_runner.py",
            "runtime/cli_v1/api.py", "runtime/cli_v1/observe.py",
            "runtime/cli_v1/review.py", "runtime/cli_v1/mcp_server.py",
            "runtime/cli_v1/__main__.py", "runtime/backends/x11_v1/backend.py",
            "runtime/backends/x11_v1/session.py", "runtime/selector_v1/selector.py"]
        source_hashes = {name: sha((ROOT / name).read_bytes()) for name in source_paths}
        write_json(EVIDENCE / "experiment-manifest.json", {
            "source_commit": os.environ["AI3548_SOURCE_COMMIT"],
            "image_id": os.environ["AI3548_IMAGE_ID"],
            "platform": subprocess.run(["uname", "-m"], capture_output=True,
                                         text=True, check=True).stdout.strip(),
            "python": sys.version,
            "versions": {"mcp": __import__("importlib.metadata", fromlist=["version"]).version("mcp"),
                         "pillow": __import__("importlib.metadata", fromlist=["version"]).version("Pillow"),
                         "python-xlib": __import__("importlib.metadata", fromlist=["version"]).version("python-xlib")},
            "source_sha256": source_hashes,
            "runtime_network": "none",
            "input_actions": 0,
            "model_calls": 0})
        manifest = {path.relative_to(EVIDENCE).as_posix(): sha(path.read_bytes())
            for path in sorted(EVIDENCE.rglob("*")) if path.is_file()}
        write_json(EVIDENCE / "raw-sha256.json", manifest)
        return 0
    finally:
        if openbox is not None:
            openbox.terminate()
            openbox.wait(timeout=3)
        display.terminate()
        display.wait(timeout=3)


if __name__ == "__main__":
    raise SystemExit(main())

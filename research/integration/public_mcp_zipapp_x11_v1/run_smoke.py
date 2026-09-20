"""One primary stdio MCP use of the committed portable zipapp on owned Xvfb."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ImageContent, TextContent


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--display", default=":91")
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    probe = subprocess.run(["xdpyinfo", "-display", args.display], capture_output=True, text=True)
    if probe.returncode:
        raise RuntimeError(f"selected X display is unavailable: {probe.stderr.strip()}")

    with tempfile.TemporaryDirectory(prefix="portable-mcp-x11-") as temp:
        root = Path(temp)
        xenv = dict(os.environ, DISPLAY=args.display)
        fixture = None
        try:
            meta, effect = root / "meta.json", root / "effect.json"
            fixture_env = dict(xenv, PYTHONPATH=str(args.fixture.parent.parent.parent))
            fixture = subprocess.Popen([args.python, str(args.fixture), "--meta", str(meta), "--effect", str(effect)],
                                       cwd=root, env=fixture_env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            deadline = time.monotonic() + 5
            while not meta.exists() and time.monotonic() < deadline:
                if fixture.poll() is not None:
                    raise RuntimeError(f"fixture exited: {fixture.stderr.read().decode(errors='replace')}")
                await asyncio.sleep(.05)
            target_id = json.loads(meta.read_text())["window_id"]
            targets = root / "targets.json"
            targets.write_text(json.dumps({"fixture": target_id}), encoding="utf-8")
            receipt_dir = root / "receipts"

            # Deliberately discard repository import paths: the server executes only the .pyz.
            server_env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL") if key in os.environ}
            server_env["DISPLAY"] = args.display
            params = StdioServerParameters(
                command=args.python,
                args=[str(args.archive.resolve()), "mcp", "--targets", str(targets),
                      "--output-directory", str(receipt_dir), "--display", args.display],
                cwd=str(root), env=server_env,
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    names = {tool.name for tool in (await session.list_tools()).tools}
                    assert names == {"interface_observe", "interface_dispatch"}, names
                    initial = await session.call_tool("interface_observe", {
                        "target": "fixture", "frame": "window_client", "region": [0, 0, 400, 180]})
                    initial_text = next(block.text for block in initial.content if isinstance(block, TextContent))
                    initial_report = json.loads(initial_text)
                    initial_images = [block for block in initial.content if isinstance(block, ImageContent)]
                    assert initial_report.get("image_status") == "image", initial_report
                    assert len(initial_images) == 1, len(initial_images)

                    program = {
                        "schema": "agent-interface/program-v1",
                        "program_id": "portable-mcp-smoke-01",
                        "source": {"observation_seq": 1, "binding_revision": 0},
                        "authority": {"lease_id": "portable-mcp-smoke", "expires_at_ns": time.monotonic_ns() + 30_000_000_000},
                        "terminal": {"release_all_required": True},
                        "ops": [
                            {"op": "focus", "target": "fixture"},
                            {"op": "pointer_move", "frame": "window_client", "x": 60, "y": 55},
                            {"op": "pointer_button", "button": "left", "down": True},
                            {"op": "pointer_button", "button": "left", "down": False},
                            {"op": "text", "text": "portable-mcp-01"},
                            {"op": "key_chord", "keys": ["CTRL", "S"]},
                            {"op": "wait_update", "timeout_ms": 100},
                            {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 400, "h": 180},
                            {"op": "release_all"},
                        ],
                    }
                    action = await session.call_tool("interface_dispatch", {
                        "program": program, "current_observation_seq": 1, "current_binding_revision": 0})
                    action_text = next(block.text for block in action.content if isinstance(block, TextContent))
                    action_report = json.loads(action_text)
                    action_images = [block for block in action.content if isinstance(block, ImageContent)]
                    # Allow Tk's independent file write to become visible; never call dispatch again.
                    deadline = time.monotonic() + 2
                    while not effect.exists() and time.monotonic() < deadline:
                        await asyncio.sleep(.02)
                    effect_data = json.loads(effect.read_text(encoding="utf-8")) if effect.exists() else None
                    report_files = sorted(receipt_dir.glob("*/report.json"))
                    retained = json.loads((Path(action_report["call_directory"]) / "report.json").read_text(encoding="utf-8"))
                    api_result = retained.get("result", {})
                    execution = api_result.get("execution", {})
                    releases = execution.get("releases", [])
                    result = {
                        "schema": "agent-interface/public-mcp-portable-smoke-v1",
                        "archive_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
                        "python": sys.version.split()[0], "mcp_sdk": "1.30.0",
                        "tool_names": sorted(names),
                        "initial_observe": {"status": initial_report.get("image_status"), "image_blocks": len(initial_images)},
                        "dispatch": {"status": action_report.get("outcome_summary", {}).get("reported_status"),
                                     "execution_status": action_report.get("outcome_summary", {}).get("execution_status"),
                                     "image_status": action_report.get("image_status"),
                                     "image_blocks": len(action_images),
                                     "retained_report_count": len(report_files),
                                     "release_verified": any(r.get("verified") for r in releases)},
                        "independent_effect": effect_data,
                        "claims": {"one_dispatch": True, "automatic_replay": False, "model_or_provider_used": False,
                                   "host_presentation_or_model_visible_feedback_measured": False,
                                   "docker_desktop_used": False},
                    }
                    result_text = json.dumps(result, indent=2, sort_keys=True) + "\n"
                    if args.result:
                        args.result.parent.mkdir(parents=True, exist_ok=True)
                        args.result.write_text(result_text, encoding="utf-8")
                    print(result_text)
                    assert effect_data == {"saved": True, "text": "portable-mcp-01"}, effect_data
                    assert len(action_images) == 1, len(action_images)
                    assert result["dispatch"]["release_verified"] is True, result
                    assert result["dispatch"]["retained_report_count"] == 2, result
                    return 0
        finally:
            if fixture is not None:
                fixture.terminate()
                try:
                    fixture.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    fixture.kill(); fixture.wait()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

"""Exercise spawned and stdio MCP clocks without opening a GUI backend."""
from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import multiprocessing
from pathlib import Path
import sys
import time

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from .execution_clock_preflight import require_same_host_qpc_clock


def clock_sample():
    return {"executable": sys.executable, "version": sys.version,
            "clock_info": vars(time.get_clock_info("monotonic")),
            "monotonic_ns": time.monotonic_ns()}


def child_sample(connection):
    try:
        connection.send(clock_sample())
    finally:
        connection.close()


async def probe(output):
    output.mkdir(parents=True, exist_ok=True)
    parent = clock_sample()
    ctx = multiprocessing.get_context("spawn")
    reader, writer = ctx.Pipe(duplex=False)
    child = ctx.Process(target=child_sample, args=(writer,), daemon=True)
    before = time.monotonic_ns()
    child.start()
    writer.close()
    try:
        if not reader.poll(15):
            raise TimeoutError("spawned clock sample missing")
        sample = reader.recv()
        after = time.monotonic_ns()
        child.join(5)
        if (child.exitcode != 0 or sample["executable"] != parent["executable"]
                or sample["clock_info"] != parent["clock_info"]
                or not before <= sample["monotonic_ns"] <= after):
            raise ValueError("spawned interpreter/clock/bracket mismatch")
    finally:
        if child.is_alive():
            child.terminate()
            child.join(5)
        reader.close()
    targets = output / "clock-only-targets.json"
    with targets.open("x", encoding="utf-8") as stream:
        json.dump({"clock_only_unopened": 123}, stream)
    root = Path(__file__).resolve().parents[3]
    parameters = StdioServerParameters(command=sys.executable,
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets),
              "--output-directory", str(output / "clock-only-server-output")],
        cwd=str(root))
    replies = []
    identity = None
    with (output / "clock-only-server-stderr.log").open("x", encoding="utf-8") as errlog:
        async with stdio_client(parameters, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for _ in range(2):
                    left = time.monotonic_ns()
                    response = await session.call_tool("interface_clock", {})
                    right = time.monotonic_ns()
                    if response.isError or len(response.content) != 1:
                        raise ValueError("clock-only MCP response failed")
                    raw = json.loads(response.content[0].text)
                    check = require_same_host_qpc_clock(raw, parent["clock_info"],
                        left, right, expected_server_instance_id=identity)
                    identity = check["server_instance_id"]
                    replies.append({"raw": raw, "qualification": check})
    report = {"parent": parent, "spawned_child": sample,
              "child_exitcode": child.exitcode,
              "child_bracket_ns": [before, after], "mcp_samples": replies,
              "packages": {name: importlib.metadata.version(name)
                           for name in ("mcp", "pydantic", "Pillow", "numpy")},
              "input_dispatched": False, "gui_backend_opened": False,
              "scope": "clock/interpreter/stdio qualification; no release or task test"}
    with (output / "clock-preflight.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "qualified", "child_exitcode": child.exitcode,
                      "mcp_samples": len(replies), "input_dispatched": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    asyncio.run(probe(parser.parse_args().output))

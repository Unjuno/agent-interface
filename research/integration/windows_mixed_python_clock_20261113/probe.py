"""Read-only clock-coordinate probe across Windows CPython installations."""
import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def child_clock_info(interpreter):
    code = (
        "import json,sys,time; print(json.dumps({"
        "'version':sys.version, 'executable':sys.executable,"
        "'clock_info':vars(time.get_clock_info('monotonic')),"
        "'monotonic_ns':time.monotonic_ns()}))"
    )
    return json.loads(subprocess.check_output(
        [interpreter, "-c", code], text=True).strip())


async def sample(parent_info, child_info, output_dir):
    repo = Path(__file__).resolve().parents[3]
    run_dir = Path(output_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    targets = run_dir / "targets.json"
    targets.write_text('{"fixture":123}', encoding="utf-8")
    receipts = run_dir / "receipts"
    params = StdioServerParameters(command=child_info["executable"], cwd=str(repo),
        args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets),
              "--output-directory", str(receipts), "--display", "not-a-valid-display"])
    rows = []
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            tools = await client.list_tools()
            clock_tool = next(item for item in tools.tools
                              if item.name == "interface_clock")
            for index in range(8):
                before = time.monotonic_ns()
                reply = await client.call_tool("interface_clock", {})
                after = time.monotonic_ns()
                if reply.isError:
                    raise RuntimeError("clock call returned MCP error")
                response = json.loads(reply.content[0].text)
                rows.append({"index": index, "parent_before_ns": before,
                    "server_ns": response["monotonic_ns"], "parent_after_ns": after,
                    "server_minus_parent_before_ns": response["monotonic_ns"]-before,
                    "server_minus_parent_after_ns": response["monotonic_ns"]-after,
                    "inside_parent_bracket": before <= response["monotonic_ns"] <= after,
                    "server_instance_id": response["server_instance_id"],
                    "clock": response["clock"],
                    "input_dispatched": response["input_dispatched"],
                    "authority_granted": response["authority_granted"],
                    "lease_issued": response["lease_issued"]})
            schema = clock_tool.inputSchema
    return {"schema": "agent-interface/mixed-python-clock-probe-v1",
        "source_commit": subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
        "parent": parent_info, "child": child_info, "clock_tool_schema": schema,
        "sample_count": len(rows), "samples": rows,
        "all_samples_inside_parent_brackets": all(r["inside_parent_bracket"] for r in rows),
        "stable_server_instance": len({r["server_instance_id"] for r in rows}) == 1,
        "all_calls_input_and_authority_free": all(
            r["input_dispatched"] is False and r["authority_granted"] is False
            and r["lease_issued"] is False for r in rows),
        "receipt_directory_entries": sorted(p.name for p in receipts.iterdir())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-python", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    parent_info = {"version": sys.version, "executable": sys.executable,
        "clock_info": vars(time.get_clock_info("monotonic"))}
    child_info = child_clock_info(args.server_python)
    result = asyncio.run(sample(parent_info, child_info, args.output))
    encoded = json.dumps(result, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    output = Path(args.output).resolve() / "mixed-clock-samples.json"
    output.write_bytes(encoded)
    print(json.dumps({"result": str(output), "sha256": hashlib.sha256(encoded).hexdigest(),
        "all_samples_inside_parent_brackets": result["all_samples_inside_parent_brackets"],
        "stable_server_instance": result["stable_server_instance"],
        "all_calls_input_and_authority_free": result["all_calls_input_and_authority_free"],
        "receipt_directory_entries": result["receipt_directory_entries"]}, indent=2))


if __name__ == "__main__":
    main()

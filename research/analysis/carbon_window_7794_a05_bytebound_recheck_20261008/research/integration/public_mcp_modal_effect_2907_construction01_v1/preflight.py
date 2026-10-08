"""Networkless, display-free public-MCP validation-shape construction test."""
import asyncio
import json
import tempfile
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from runner import DISPLAY, ENV, program


async def main():
    output = Path(tempfile.mkdtemp(prefix="modal-effect-preflight-"))
    targets = output / "targets.json"
    targets.write_text(json.dumps({"calc": 1}), encoding="utf-8")
    params = StdioServerParameters(
        command="python3", args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets),
            "--output-directory", str(output / "receipts"), "--display", DISPLAY,
            "--session-mode", "persistent-x11"], env=ENV, cwd="/opt/importroot")
    valid = []
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:
            await client.initialize()
            for pid, chord in (("preflight-open", ["CTRL", "O"]),
                               ("preflight-escape", ["ESC"]),
                               ("preflight-f6", ["F6"])):
                draft = program(pid, 1, 1, chord)
                result = await client.call_tool("interface_validate", {"program": draft})
                texts = [item.text for item in result.content if getattr(item, "type", None) == "text"]
                payload = json.loads(texts[0]) if len(texts) == 1 else {}
                valid.append({"program_id": pid, "static_valid": payload.get("static_valid"),
                              "backend_checked": payload.get("backend_checked"),
                              "runtime_admission": payload.get("runtime_admission"),
                              "input_dispatched": payload.get("input_dispatched")})
    expected = all(row["static_valid"] is True and row["backend_checked"] is False and
                   row["runtime_admission"] == "not_evaluated" and
                   row["input_dispatched"] is False for row in valid)
    print(json.dumps({"decision": "PASS_STATIC_PUBLIC_MCP_VALIDATION" if expected else "FAIL_STATIC_PUBLIC_MCP_VALIDATION",
                      "display_opened": False, "input_dispatched": False, "rows": valid}, sort_keys=True))
    if not expected:
        raise SystemExit(2)


if __name__ == "__main__":
    asyncio.run(main())

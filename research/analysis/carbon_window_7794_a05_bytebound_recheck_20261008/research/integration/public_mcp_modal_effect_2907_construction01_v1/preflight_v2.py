"""Versioned networkless, display-free MCP program-shape preflight."""
import asyncio
import json
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from runner import DISPLAY, ENV, program


async def main():
    output = Path(tempfile.mkdtemp(prefix="modal-effect-preflight-v2-"))
    targets = output / "targets.json"
    targets.write_text(json.dumps({"calc": 1}), encoding="utf-8")
    params = StdioServerParameters(
        command="python3", args=["-m", "runtime.cli_v1.mcp_server", "--targets", str(targets),
            "--output-directory", str(output / "receipts"), "--display", DISPLAY,
            "--session-mode", "persistent-x11"], env=ENV, cwd="/opt/importroot")
    rows = []
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:
            await client.initialize()
            for pid, chord in (("preflight-open", ["CTRL", "O"]),
                               ("preflight-escape", ["ESC"]),
                               ("preflight-f6", ["F6"])):
                result = await client.call_tool("interface_validate", {
                    "program": program(pid, 1, 1, chord)})
                texts = [item.text for item in result.content if getattr(item, "type", None) == "text"]
                payload = json.loads(texts[0]) if len(texts) == 1 else {}
                rows.append({"program_id": pid, "static_valid": payload.get("static_valid"),
                             "backend_checked": payload.get("backend_checked"),
                             "runtime_admission": payload.get("runtime_admission"),
                             "input_dispatched": payload.get("input_dispatched")})
    accepted = all(row["static_valid"] is True and row["backend_checked"] is False and
                   row["runtime_admission"] == "not_evaluated" and
                   row["input_dispatched"] is None for row in rows)
    print(json.dumps({"decision": "PASS_STATIC_PUBLIC_MCP_VALIDATION_V2" if accepted else
                      "FAIL_STATIC_PUBLIC_MCP_VALIDATION_V2", "display_opened": False,
                      "input_dispatched": False, "rows": rows}, sort_keys=True))
    if not accepted:
        raise SystemExit(2)


if __name__ == "__main__":
    asyncio.run(main())

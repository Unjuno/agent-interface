"""Engineering characterization: exact relay sources and an inert SDK-shaped client."""
import asyncio
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp.types import CallToolResult


class Client:
    def __init__(self):
        self.calls = []

    async def call_tool(self, tool, arguments):
        self.calls.append(arguments)
        return CallToolResult(content=[])


async def main():
    root = Path(__file__).resolve().parent
    cases = json.loads((root / "cases.json").read_bytes())
    rows = []
    started = datetime.now(timezone.utc).isoformat()
    for variant in ("baseline", "candidate"):
        path = root / "source" / (variant + "_relay.py")
        spec = importlib.util.spec_from_file_location("probe_" + variant, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for case in cases:
            client = Client()
            relay = module.Relay(client)
            line = '{"id":1,"tool":"interface_dispatch","arguments":{"value":' + case["literal"] + '}}'
            response = await relay.request(line)
            call_count = len(client.calls)
            try:
                received_json = json.dumps(client.calls[0], allow_nan=False, sort_keys=True) if client.calls else None
                serialization = "finite" if client.calls else "not_dispatched"
            except ValueError:
                received_json = None
                serialization = "nonfinite"
            followup = await relay.request('{"id":1,"tool":"interface_dispatch","arguments":{}}')
            rows.append({"variant":variant, "case":case["name"], "line":line,
                         "response":response, "call_count":call_count,
                         "received_json":received_json, "serialization":serialization,
                         "same_id_followup":followup, "total_calls":len(client.calls)})
    result = {"schema":"relay-finite-json-construction-v1", "started_at":started,
              "ended_at":datetime.now(timezone.utc).isoformat(),
              "python":sys.version, "platform":platform.platform(),
              "mcp":importlib.metadata.version("mcp"),
              "sources":{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (root / "source").glob("*.py")},
              "cases_sha256":hashlib.sha256((root / "cases.json").read_bytes()).hexdigest(),
              "rows":rows}
    print(json.dumps(result, allow_nan=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())

"""Measure prevalidation overhead on a no-op registered MCP tool."""
import asyncio
import importlib.metadata
import json
import math
import platform
import statistics
import time

from mcp.server.fastmcp import FastMCP
from runtime.cli_v1.mcp_server import PublicArgumentMCP, content


class PriorPublicArgumentMCP(FastMCP):
    """#10182 behavior: top-level required/unknown checks, no Pydantic preflight."""

    async def list_tools(self):
        tools = await super().list_tools()
        return [tool.model_copy(update={
            "inputSchema": {**tool.inputSchema, "additionalProperties": False}
        }) for tool in tools]

    async def call_tool(self, name, arguments):
        for tool in await self.list_tools():
            if tool.name == name:
                schema = tool.inputSchema
                properties = schema.get("properties", {})
                unknown = sorted(set(arguments) - set(properties))
                if unknown:
                    return content({"status": "invalid_request",
                                    "error": "unknown top-level tool arguments",
                                    "unknown_arguments": unknown,
                                    "operation_invoked": False,
                                    "input_dispatched": False,
                                    "replay_allowed": False}, error=True)
                missing = sorted(set(schema.get("required", ())) - set(arguments))
                if missing:
                    return content({"status": "invalid_request",
                                    "error": "missing required tool arguments",
                                    "missing_arguments": missing,
                                    "operation_invoked": False,
                                    "input_dispatched": False,
                                    "release_confirmed": None,
                                    "effect_status": "unknown",
                                    "task_success": None,
                                    "replay_allowed": False}, error=True)
                break
        return await super().call_tool(name, arguments)


async def add_tool(server, call_counter):
    @server.tool()
    async def no_op(value: int, items: list[int]) -> dict:
        call_counter[0] += 1
        return {"total": value + sum(items)}


async def run():
    baseline_calls = [0]
    candidate_calls = [0]
    baseline = PriorPublicArgumentMCP("baseline")
    candidate = PublicArgumentMCP("candidate")
    await add_tool(baseline, baseline_calls)
    await add_tool(candidate, candidate_calls)
    name = "no_op"
    arguments = {"value": 7, "items": [1, 2, 3, 4]}
    expected = json.loads((await baseline.call_tool(name, arguments))[0].text)
    actual = json.loads((await candidate.call_tool(name, arguments))[0].text)
    if expected != actual or expected.get("total") != 17:
        raise AssertionError((expected, actual))

    warmup = 100
    batches = 40
    calls_per_batch = 100
    for _ in range(warmup):
        await baseline.call_tool(name, arguments)
        await candidate.call_tool(name, arguments)

    samples = {"baseline": [], "candidate": []}
    servers = {"baseline": baseline, "candidate": candidate}
    for batch in range(batches):
        order = ("baseline", "candidate") if batch % 2 == 0 else (
            "candidate", "baseline")
        for label in order:
            started = time.perf_counter_ns()
            response = None
            for _ in range(calls_per_batch):
                response = await servers[label].call_tool(name, arguments)
            elapsed = time.perf_counter_ns() - started
            if (not isinstance(response, (list, tuple)) or not response
                    or json.loads(response[0].text) != expected):
                raise AssertionError((label, response))
            samples[label].append(elapsed / calls_per_batch / 1_000_000)

    def summary(values):
        ordered = sorted(values)
        return {
            "batch_mean_ms": statistics.mean(values),
            "batch_median_ms": statistics.median(values),
            "batch_p95_ms": ordered[math.ceil(0.95 * len(ordered)) - 1],
            "batch_min_ms": min(values),
            "batch_max_ms": max(values),
        }

    base = summary(samples["baseline"])
    current = summary(samples["candidate"])
    print(json.dumps({
        "benchmark": "public_argument_pydantic_preflight_overhead_v1",
        "scope": "in-process FastMCP no-op tool; no GUI, provider, or input",
        "python": platform.python_version(),
        "mcp": importlib.metadata.version("mcp"),
        "pydantic": importlib.metadata.version("pydantic"),
        "warmup_calls_per_arm": warmup,
        "paired_batches": batches,
        "calls_per_batch_per_arm": calls_per_batch,
        "orders": "alternating baseline/candidate order per paired batch",
        "returned_value": expected,
        "baseline_handler_calls": baseline_calls[0],
        "candidate_handler_calls": candidate_calls[0],
        "baseline": base,
        "candidate": current,
        "median_delta_percent": 100 * (
            current["batch_median_ms"] / base["batch_median_ms"] - 1),
        "batch_medians_ms": samples,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(run())

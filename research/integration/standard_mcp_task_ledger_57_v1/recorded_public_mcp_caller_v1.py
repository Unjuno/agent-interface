"""Join one provider-generation boundary to sequential public MCP calls.

This research adapter records exactly the callable and Relay bytes supplied by
its caller. A provider adapter may still hide internal retries; the journal
must not be treated as exhaustive until reconciled with independent provider
logs.
"""

import json


def _json_bytes(value):
    return json.dumps(value, allow_nan=False, separators=(",", ":"),
                      sort_keys=True).encode("utf-8")


class RecordedPublicMcpCaller:
    """Durably record provider attempts and their standard public Relay calls."""

    def __init__(self, relay, recorder):
        if not callable(getattr(relay, "request", None)):
            raise TypeError("relay must expose async request(bytes)")
        if not callable(getattr(recorder, "invoke_async", None)) or not callable(
                getattr(recorder, "invoke_tool_async", None)):
            raise TypeError("recorder must expose async provider and MCP boundaries")
        self.relay = relay
        self.recorder = recorder

    async def invoke_provider(self, attempt_id, request_bytes, provider_call):
        """Record one injected provider call before invoking it."""
        return await self.recorder.invoke_async(
            attempt_id, request_bytes, provider_call)

    async def call_tool(self, attempt_id, call_id, method, arguments):
        """Record the exact JSON request/response envelopes around Relay.request."""
        request = {"id": self.relay.next_id, "tool": method,
                   "arguments": arguments}
        request_bytes = _json_bytes(request)

        async def transport():
            response = await self.relay.request(request_bytes)
            return {"result": response, "response_bytes": _json_bytes(response)}

        return await self.recorder.invoke_tool_async(
            attempt_id, call_id, method, request_bytes, transport)

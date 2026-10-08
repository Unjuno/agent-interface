"""Fresh successor caller for allocation 02; allocation 01 remains untouched."""
import json
from pathlib import Path

import runner_effect as base


MARKER = "agent-mcp-effect-2907-20260927-02"
base.MARKER = MARKER
OUT = base.OUT


def decode_payload(text):
    payload = json.loads(text)
    if (payload.get("schema") == "agent-interface/review-v1"
            and payload.get("receipt", {}).get("schema") == "agent-interface/receipt-view-v1"):
        raw = payload.get("receipt", {}).get("source", {}).get("raw_report")
        if not isinstance(raw, dict):
            raise AssertionError("PUBLIC_RAW_REPORT_MISSING")
        return payload, raw
    if isinstance(payload, dict) and isinstance(payload.get("status"), str) and "session_id" in payload:
        return payload, payload
    raise AssertionError("UNKNOWN_PUBLIC_RESPONSE_SCHEMA")


def save_response(path, result):
    metadata = base.retained.save_mcp_response(path, result)
    text = [row.text for row in result.content if getattr(row, "type", None) == "text"]
    if len(text) != 1:
        raise AssertionError("EXPECTED_ONE_TEXT_BLOCK")
    payload, raw = decode_payload(text[0])
    return payload, raw, metadata


base.save_response = save_response


async def execute_mcp_v2(targets, html_path):
    trace = await base.execute_mcp(targets, html_path)
    effect = trace.get("effect_receipt")
    if effect:
        raw = json.dumps(effect, sort_keys=True, indent=2).encode() + b"\n"
        (OUT / "effect_receipt.json").write_bytes(raw)
    return trace


def main():
    base.execute_mcp = execute_mcp_v2
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())

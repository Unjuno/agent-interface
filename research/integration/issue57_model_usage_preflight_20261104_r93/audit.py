from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "r93-a01"
SPOOL = ROOT / "spool"
ATTEMPT_ID = "issue57-r93-a01"
USAGE_MAP = {
    "inputTokens": "input_tokens",
    "cachedInputTokens": "cached_input_tokens",
    "cacheWriteInputTokens": "cache_write_input_tokens",
    "outputTokens": "output_tokens",
    "reasoningOutputTokens": "reasoning_output_tokens",
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    result = read(ROOT / "worker-result.json")
    request_path = SPOOL / "inflight" / f"{ATTEMPT_ID}.json"
    request = read(request_path)
    protocol_path = SPOOL / "protocol.jsonl"
    rows = [json.loads(line) for line in protocol_path.read_text(encoding="utf-8").splitlines() if line]
    errors = []
    received = [row["message"] for row in rows if row.get("direction") == "received"]
    sent = [row["message"] for row in rows if row.get("direction") == "sent"]
    starts = [m for m in sent if m.get("method") == "turn/start"]
    completes = [m for m in received if m.get("method") == "turn/completed"]
    usage_rows = [m for m in received if m.get("method") == "thread/tokenUsage/updated"]
    status_rows = [m for m in sent if m.get("method") == "mcpServerStatus/list"]
    status_replies = [m for m in received if m.get("id") in {r.get("id") for r in status_rows}]
    if (request.get("attempt_id") != ATTEMPT_ID or request.get("model") != "gpt-6-luna"
            or request.get("effort") != "medium"):
        errors.append("claimed provider request differs from preregistered attempt/model/effort")
    if result.get("status") != "completed" or result.get("answer_eligible") is not True:
        errors.append("worker did not return one eligible completed turn")
    if len(starts) != 1 or len(completes) != 1:
        errors.append(f"expected one turn start and completion; got {len(starts)}/{len(completes)}")
    if starts and (starts[0].get("params", {}).get("model") != "gpt-6-luna"
            or starts[0].get("params", {}).get("effort") != "medium"):
        errors.append("turn/start model or effort differs from preregistration")
    if len(usage_rows) < 1:
        errors.append("no tokenUsage update retained")
    if not status_rows or not status_replies:
        errors.append("MCP disabled-state preflight missing from protocol journal")
    else:
        reply = status_replies[-1].get("result", {})
        servers = reply.get("data")
        if not isinstance(servers, list) or any(
                not isinstance(s, dict) or s.get("runtimeStatus") != "disabled"
                or s.get("tools") not in ([], {}) for s in servers):
            errors.append("one or more MCP servers were not explicitly disabled")
    mcp_disabled = bool(status_rows and status_replies) and all(
        isinstance(s, dict) and s.get("runtimeStatus") == "disabled"
        and s.get("tools") in ([], {})
        for s in (status_replies[-1].get("result", {}).get("data") or []))
    usage = result.get("usage")
    latest_usage = (usage_rows[-1].get("params", {}).get("tokenUsage")
                    if usage_rows else None)
    if not isinstance(usage, dict):
        errors.append("worker usage record missing")
    elif latest_usage != usage:
        errors.append("terminal App Server usage and retained tokenUsage event differ")
    raw_last = usage.get("last") if isinstance(usage, dict) else None
    mapped = ({target: raw_last.get(source) for source, target in USAGE_MAP.items()}
              if isinstance(raw_last, dict) else {})
    if set(mapped) != set(USAGE_MAP.values()) or any(
            type(value) is not int or value < 0 for value in mapped.values()):
        errors.append("one or more usage fields are missing or invalid")
    answer = result.get("answer")
    if not isinstance(answer, dict):
        errors.append("structured answer missing")
        answer = None
    plan_gates = {
        "visible_sheet": isinstance(answer, dict) and answer.get("visible_sheet") == "Sheet1",
        "selected_cell": isinstance(answer, dict) and answer.get("selected_cell") == "A1",
        "blank_cells": isinstance(answer, dict) and answer.get("cells_blank") is True,
        "planned_order": isinstance(answer, dict) and answer.get("proposed_actions") == [
            "enter_731_in_A1", "enter_864_in_A2", "save"],
        "confidence_range": isinstance(answer, dict) and type(answer.get("confidence")) in (int, float)
            and 0 <= answer["confidence"] <= 1,
        "visual_note": isinstance(answer, dict) and isinstance(answer.get("visual_note"), str),
    }
    usage_capture_passed = (result.get("status") == "completed"
        and len(starts) == 1 and len(completes) == 1 and bool(usage_rows)
        and isinstance(usage, dict) and latest_usage == usage
        and set(mapped) == set(USAGE_MAP.values())
        and all(type(value) is int and value >= 0 for value in mapped.values())
        and mcp_disabled)
    summary = {
        "schema": "agent-interface/issue57-model-usage-preflight-audit-v1",
        "attempt_id": ATTEMPT_ID,
        "status": "PASS_PROVIDER_USAGE_SCOPED" if usage_capture_passed else "FAIL_OR_UNKNOWN",
        "turn_starts": len(starts), "turn_completions": len(completes),
        "usage_events": len(usage_rows), "usage": mapped,
        "usage_capture_passed": usage_capture_passed,
        "plan_gates": plan_gates, "plan_scoped_passed": all(plan_gates.values()),
        "protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        "answer": answer, "errors": errors,
        "scope_limit": "one read-only image-planning turn; no MCP/UI action or task effect",
    }
    (ROOT / "audit.json").write_text(json.dumps(summary, sort_keys=True,
        indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())


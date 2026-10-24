from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PACKET = REPO / "research/integration/current_main_appserver_public_mcp_generation_refusal_20261025_p08"
RUN = PACKET / "run"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    protocol = [json.loads(line) for line in
                (RUN / "provider-call/model/events.jsonl").read_text(encoding="utf-8").splitlines()]
    usage = [event["message"]["params"]["tokenUsage"]["last"] for event in protocol
             if event.get("message", {}).get("method") == "thread/tokenUsage/updated"]
    turns = [event["message"]["params"]["turn"] for event in protocol
             if event.get("message", {}).get("method") == "turn/completed"]
    provider = read(RUN / "provider-call/result.json")
    ledger = read(RUN / "LEDGER-RECONCILED.json")
    result = read(RUN / "RESULT.json")
    attempt = [event for event in ledger.get("events", [])
               if event.get("kind") == "model_attempt"]
    expected = {"input_tokens": 10185, "output_tokens": 60,
                "reasoning_output_tokens": 41, "cached_input_tokens": 0,
                "cache_write_input_tokens": 0}
    proto_usage = ({"input_tokens": usage[0]["inputTokens"],
                    "output_tokens": usage[0]["outputTokens"],
                    "reasoning_output_tokens": usage[0]["reasoningOutputTokens"],
                    "cached_input_tokens": usage[0]["cachedInputTokens"],
                    "cache_write_input_tokens": usage[0]["cacheWriteInputTokens"]}
                   if len(usage) == 1 else None)
    provider_usage = ({key: provider["usage"][key] for key in expected}
                      if all(key in provider.get("usage", {}) for key in expected) else None)
    ledger_usage = ({key: attempt[0]["usage"][key] for key in expected}
                    if len(attempt) == 1 else None)
    final_text = None
    if len(turns) == 1:
        finals = [item.get("text") for item in turns[0].get("items", [])
                  if item.get("type") == "agentMessage" and item.get("phase") == "final_answer"]
        final_text = finals[-1] if finals else None
    checks = {
        "one_completed_turn": len(turns) == len(usage) == len(attempt) == 1 and turns[0].get("status") == "completed",
        "usage_matches_protocol_provider_and_ledger": proto_usage == provider_usage == ledger_usage == expected,
        "answer_matches_selected_point": final_text == '{"point":[16,8]}' and provider["raw"] == {"point": [16, 8]} and result["selected_point"] == [16, 8],
        "provider_call_completed": provider.get("turn_status") == "completed" and provider.get("answer_eligible") is True,
        "ledger_complete": ledger.get("complete") is True and result.get("ledger_complete") is True,
    }
    raw_hashes = []
    for line in (RUN / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        raw_hashes.append(hashlib.sha256((RUN / relative).read_bytes()).hexdigest() == digest)
    checks["retained_raw_hashes_match"] = bool(raw_hashes) and all(raw_hashes)
    report = {
        "schema": "agent-interface/p08-provider-usage-reconciliation-v1",
        "classification": "PASS_SCOPED" if all(checks.values()) else "FAIL_OR_HOLD",
        "checks": checks,
        "usage": expected,
        "scope": "one real App Server turn on synthetic Fake X",
        "efficiency_or_reliability_claim": False,
    }
    out = Path(__file__).with_name("AUDIT.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["classification"] != "PASS_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[3]
PACKET = REPO / "research/integration/current_main_appserver_public_mcp_visual_grounding_20261025_p07"
RUN = PACKET / "run"
SERVER = RUN / "server"
SESSION = SERVER / "guarded-session-077aece154e54fcebc255629071e2576"
COMPILED = "compiled-7cfd950e944243e09da4bd74e149cf30"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    events = [json.loads(line) for line in
              (RUN / "provider-call/model/events.jsonl").read_text(encoding="utf-8").splitlines()]
    usage_events = [e["message"]["params"]["tokenUsage"]["last"] for e in events
                    if e.get("message", {}).get("method") == "thread/tokenUsage/updated"]
    completed = [e["message"]["params"]["turn"] for e in events
                 if e.get("message", {}).get("method") == "turn/completed"]
    provider = read(RUN / "provider-call/result.json")
    ledger = read(RUN / "LEDGER-RECONCILED.json")
    result = read(RUN / "RESULT.json")
    raw_score = next(e for e in ledger["events"] if e.get("kind") == "task_score")
    attempt = next(e for e in ledger["events"] if e.get("kind") == "model_attempt")
    selected = read(RUN / "model-selected-point.json")
    mint_request = read(RUN / "model-derived-mint-request.json")
    mint_receipt = read(SESSION / "mint-grounded_green.json")
    click = read(SERVER / "synthetic-target-click.json")
    effect = read(SERVER / "synthetic-effect-receipt.json")
    terminal = read(SESSION / f"{COMPILED}-11-terminal.json")
    receipt = read(SESSION / f"{COMPILED}-19-receipt.json")
    close = read(SERVER / "session-077aece154e54fcebc255629071e2576-close.json")
    pixel = list(Image.frombytes("RGB", (32, 32),
                                 (SERVER / "synthetic-application-state.rgb").read_bytes(),
                                 "raw", "BGRX").getpixel((1, 1)))
    usage = {"input_tokens": 10185, "output_tokens": 58,
             "reasoning_output_tokens": 39, "cached_input_tokens": 0,
             "cache_write_input_tokens": 0}
    protocol_usage = ({
        "input_tokens": usage_events[0]["inputTokens"],
        "output_tokens": usage_events[0]["outputTokens"],
        "reasoning_output_tokens": usage_events[0]["reasoningOutputTokens"],
        "cached_input_tokens": usage_events[0]["cachedInputTokens"],
        "cache_write_input_tokens": usage_events[0]["cacheWriteInputTokens"],
    } if len(usage_events) == 1 else None)
    provider_usage = {k: provider["usage"][k] for k in usage}
    ledger_usage = {k: attempt["usage"][k] for k in usage}
    checks = {
        "ledger_complete": ledger.get("complete") is True,
        "exactly_one_completed_turn": len(completed) == len(usage_events) == 1 and completed[0]["status"] == "completed",
        "protocol_provider_ledger_usage_agree": protocol_usage == provider_usage == ledger_usage == usage,
        "model_turn_point_matches_saved_selection": json.loads(completed[0]["items"][-1]["text"]) == {"point": [16, 8]} and selected["point"] == [16, 8],
        "initial_ledger_false_score_preserved": raw_score["task_success"] is False and result["independent_task_success"] is False,
        "observation_mint_sequence_reconciles": mint_request["source_sequence"] == result["observation_sequence"] == mint_receipt["created_sequence"] == 1,
        "owner_click_and_effect_reconcile": click["event"]["point"] == selected["point"] == effect["click_point"] and effect["button_press_count"] == 1,
        "persisted_effect_pixel_is_success": pixel == effect["rgb"] == [255, 0, 0],
        "compiled_receipt_and_terminal_reconcile": receipt["outcome"] == "TASK_SUCCEEDED" and terminal["status"] == "completed" and terminal["release"]["verified"] is True,
        "close_release_confirmed": close["verified"] is True and close["release_confirmed"] is True,
        "runtime_task_success_untouched": result["runtime_task_success"] is None,
    }
    raw_checks = []
    for line in (RUN / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        raw_checks.append(hashlib.sha256((RUN / relative).read_bytes()).hexdigest() == digest)
    checks["all_retained_raw_hashes_match"] = bool(raw_checks) and all(raw_checks)
    report = {
        "schema": "agent-interface/p07-provider-ledger-rescore-reconciliation-v1",
        "classification": "PASS_SCOPED" if all(checks.values()) else "FAIL_OR_HOLD",
        "checks": checks,
        "original_ledger_score": False,
        "posthoc_evidence_rescore": all(checks.values()),
        "rescore_relationship": "The raw ledger score remains false and unchanged; the additive auditor uses separately retained owner click/effect/pixel and release receipts to correct the score. This report does not rewrite the historical run or runtime task_success.",
        "scope": "one real model turn, standard public MCP, synthetic Fake X only",
        "efficiency_or_reliability_claim": False,
    }
    out = Path(__file__).with_name("AUDIT.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["classification"] != "PASS_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

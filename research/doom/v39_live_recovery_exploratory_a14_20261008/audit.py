"""Recompute A14 facts from retained V39 controller and session artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_protocol_deviation(freeze, adapter, runtime_sources, actual_turn_count):
    no_turn_expected = "no planner turn or model call" in freeze.get("purpose", "")
    diagnostic = freeze.get("diagnostic_adapter", {})
    expected_sha = diagnostic.get("diagnostic_sha256")
    adapter_path = adapter.get("file", "")
    runtime_path = adapter_path.removeprefix("research/")
    actual_sha = runtime_sources.get(runtime_path)
    reasons = {
        "planner_turns_when_forbidden": no_turn_expected and actual_turn_count > 0,
        "declared_diagnostic_source_not_executed": (
            no_turn_expected and expected_sha is not None and actual_sha != expected_sha
        ),
    }
    return reasons, any(reasons.values()), expected_sha, actual_sha


def main() -> int:
    freeze = load_json(ROOT / "ORIGINAL_FREEZE.json")
    report = load_json(RAW / "report.json")
    runtime = jsonl(RAW / "runtime" / "events.jsonl")
    protocol = jsonl(RAW / "planner-protocol.jsonl")
    source_manifest = load_json(ROOT / "STAGED_SOURCE_MANIFEST_708ca59a.json")
    manifest_by_path = {row["path"]: row for row in source_manifest}
    runtime_sources = load_json(RAW / "runtime" / "sources.json")
    adapter = load_json(ROOT / "DIAGNOSTIC_ADAPTER.json")
    source_mismatches = []
    for relative_path, runtime_sha in runtime_sources.items():
        manifest_path = f"research/{relative_path}"
        manifest_row = manifest_by_path.get(manifest_path)
        expected_sha = None if manifest_row is None else manifest_row["staged_sha256"]
        if manifest_path == adapter["file"]:
            expected_sha = adapter["diagnostic_sha256"] or adapter["executed_sha256"]
        if expected_sha != runtime_sha:
            source_mismatches.append(
                {"path": manifest_path, "expected": expected_sha, "runtime": runtime_sha}
            )

    started = {
        row["message"]["params"]["turn"]["id"]
        for row in protocol
        if row.get("direction") == "received"
        and row.get("message", {}).get("method") == "turn/started"
    }
    completed = {}
    for row in protocol:
        message = row.get("message", {})
        if row.get("direction") == "received" and message.get("method") == "turn/completed":
            turn = message.get("params", {}).get("turn", {})
            completed[turn.get("id")] = {
                "status": turn.get("status"),
                "observed_ns": row.get("observed_ns"),
            }

    invalidation_rows = []
    checks = {}
    for decision in report["decisions"]:
        invalidation = decision.get("policy_invalidation")
        if not invalidation:
            continue
        outcomes = invalidation.get("outcomes", {})
        health = outcomes.get("health", {})
        ammo = outcomes.get("ammo", {})
        turn_id = decision.get("planner_turn_id")
        turn_completion = completed.get(turn_id, {})
        cover_id = f"cover-{decision['iteration']}"
        release = next(
            (row for row in runtime if row.get("event") == "input_released" and row.get("id") == cover_id),
            None,
        )
        terminal = next(
            (row for row in runtime if row.get("event") == "terminal" and row.get("id") == cover_id),
            None,
        )
        release_receipt = (release or {}).get("owner_release", {})
        terminal_receipt = (terminal or {}).get("release", {})
        source_health = health.get("source_value")
        current_health = health.get("current_value")
        hard_floor = health.get("hard_minimum")
        current_ammo = ammo.get("current_value")
        release_ns = (release or {}).get("published_ns")
        terminal_ns = (terminal or {}).get("emit_ns")
        order_ok = bool(
            turn_completion.get("status") == "interrupted"
            and turn_completion.get("observed_ns")
            and release_ns
            and terminal_ns
            and turn_completion["observed_ns"] < release_ns < terminal_ns
        )
        empty_release = bool(
            release_receipt.get("verified") is True
            and release_receipt.get("buttons_down") == []
            and release_receipt.get("keys_down") == []
            and release_receipt.get("keys_unknown") == []
            and release_receipt.get("key_state_errors") == []
            and terminal_receipt.get("verified") is True
            and terminal_receipt.get("buttons_down") == []
            and terminal_receipt.get("keys_down") == []
            and terminal_receipt.get("keys_unknown") == []
            and terminal_receipt.get("key_state_errors") == []
        )
        no_hard_crossing = bool(
            source_health == current_health
            and isinstance(hard_floor, int)
            and current_health is not None
            and current_health >= hard_floor
            and isinstance(current_ammo, int)
            and current_ammo >= 1
            and invalidation.get("reason") == "health:source_expired"
        )
        invalidation_rows.append(
            {
                "iteration": decision["iteration"],
                "cover_id": cover_id,
                "source_health": source_health,
                "current_health": current_health,
                "hard_health_floor": hard_floor,
                "source_age_ms": health.get("source_age_ms"),
                "source_ammo": ammo.get("source_value"),
                "current_ammo": current_ammo,
                "reason": invalidation.get("reason"),
                "planner_terminal": turn_completion.get("status"),
                "answer_eligible": decision.get("planner_answer_eligible"),
                "discard_reason": decision.get("discard_reason"),
                "final_admission": (decision.get("final_action_admission") or {}).get("status"),
                "release_verified_empty": empty_release,
                "interrupt_completion_before_release_before_terminal": order_ok,
                "hard_boundary_crossing": not no_hard_crossing,
            }
        )

    actual_turn_count = len(started)
    protocol_deviation_reasons, protocol_deviation, expected_diagnostic_sha, actual_session_sha = (
        classify_protocol_deviation(freeze, adapter, runtime_sources, actual_turn_count)
    )
    score = report.get("score", {})
    decisions_by_iteration = {d["iteration"]: d for d in report["decisions"]}
    recovery_3 = decisions_by_iteration.get(3, {})
    recovery_4 = decisions_by_iteration.get(4, {})
    checks = {
        "six_started_turns_match_report": actual_turn_count == report.get("planner_turns") == 6,
        "two_source_expiry_interruptions": len(invalidation_rows) == 2
        and all(row["reason"] == "health:source_expired" for row in invalidation_rows),
        "both_answers_ineligible_and_discarded": all(
            row["answer_eligible"] is False
            and row["final_admission"] == "REJECTED_POLICY_INVALIDATED"
            for row in invalidation_rows
        ),
        "both_interrupt_release_terminal_orders_observed": all(
            row["interrupt_completion_before_release_before_terminal"] for row in invalidation_rows
        ),
        "both_per_key_releases_verified_empty": all(
            row["release_verified_empty"] for row in invalidation_rows
        ),
        "neither_invalidation_crossed_health_or_ammo_hard_floor": all(
            not row["hard_boundary_crossing"] for row in invalidation_rows
        ),
        "fresh_turn_3_answer_rejected_as_not_current": recovery_3.get("final_action_admission", {}).get("status")
        == "REJECTED_ACTION_NOT_CURRENT",
        "later_turn_4_action_admitted": recovery_4.get("final_action_admission", {}).get("status")
        == "INPUT_ADMITTED",
        "terminal_score_no_death_kill_or_map_exit": score.get("player_dead") is False
        and score.get("death_count") == 0
        and score.get("kill_count") == 0
        and score.get("map_exit") is False,
        "original_freeze_mismatch_detected": protocol_deviation,
        "runtime_source_hashes_match_staged_manifest_or_diagnostic_adapter": not source_mismatches,
    }
    if not all(checks.values()):
        status = "AUDIT_CHECK_FAILED"
    elif protocol_deviation:
        status = "EXPLORATORY_PROTOCOL_DEVIATION"
    else:
        status = "BOUNDED_OBSERVATION"

    audit = {
        "schema": "map01-v39-live-a14-audit-v2",
        "status": status,
        "freeze_source_main": freeze.get("source_main"),
        "frozen_purpose": freeze.get("purpose"),
        "actual_planner_turns": actual_turn_count,
        "reported_planner_turns": report.get("planner_turns"),
        "planner_interruptions": report.get("planner_interruption_requests"),
        "planner_interrupted_completions": report.get("planner_interrupted_completions"),
        "policy_invalidations": invalidation_rows,
        "post_invalidation_turn3": {
            "status": recovery_3.get("final_action_admission", {}).get("status"),
            "discard_reason": recovery_3.get("discard_reason"),
        },
        "post_invalidation_turn4": {
            "status": recovery_4.get("final_action_admission", {}).get("status"),
            "action": (recovery_4.get("action") or {}).get("commands"),
        },
        "score": score,
        "protocol_deviation_reasons": protocol_deviation_reasons,
        "declared_diagnostic_source_sha256": expected_diagnostic_sha,
        "runtime_diagnostic_source_sha256": actual_session_sha,
        "runtime_source_hash_mismatches": source_mismatches,
        "diagnostic_adapter_executed": adapter["diagnostic_sha256"] is not None
        and runtime_sources.get("doom/session_map01_v12.py") == adapter["diagnostic_sha256"],
        "raw_file_count": sum(1 for path in RAW.rglob("*") if path.is_file()),
        "raw_total_bytes": sum(path.stat().st_size for path in RAW.rglob("*") if path.is_file()),
        "raw_report_sha256": sha256(RAW / "report.json"),
        "runtime_event_stream_sha256": sha256(RAW / "runtime" / "events.jsonl"),
        "planner_protocol_sha256": sha256(RAW / "planner-protocol.jsonl"),
        "checks": checks,
        "scope": "Raw consistency audit only. The freeze mismatch invalidates preregistered efficacy claims; the threat-triggered health/ammo gate was not reached.",
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": checks}, indent=2))
    return 0 if status != "AUDIT_CHECK_FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

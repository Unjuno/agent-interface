"""Standalone raw-only auditor for Issue #6561 construction packets."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


EXPECTED_CASES = {"NONE", "ONE_SOFT", "MULTI_SOFT", "HARD", "UNKNOWN", "EXPIRED"}
CONTEXT_KEYS = {
    "state", "sequence", "signal_id", "source_value", "current_value",
    "source_age_ms", "guard_id", "outcome", "soft_event_count",
    "grants_input_authority", "task_success_verified",
}
PROMPT_PREFIX = "Latest observed soft evidence (advisory only): "


def _unknown(reason: str) -> dict:
    return {"state": "UNKNOWN", "reason": reason}


def _derive_observed(case: dict) -> dict:
    events = case["raw_events"]
    current_sequence = case["current_sequence"]
    binding = case["binding"]
    if type(current_sequence) is not int or current_sequence < 0:
        return _unknown("invalid_current_sequence")
    if not isinstance(events, list) or not events:
        return _unknown("missing_raw_history")
    if len(events) > 128:
        return _unknown("oversized_raw_history")

    previous_sequence = -1
    for event in events:
        if not isinstance(event, dict):
            return _unknown("malformed_event")
        sequence = event.get("sequence")
        signal = event.get("signal")
        outcome = event.get("outcome")
        if type(sequence) is not int or sequence < 0 or sequence <= previous_sequence:
            return _unknown("invalid_event_order")
        if sequence >= current_sequence:
            return _unknown("nonprior_event")
        if not isinstance(signal, dict) or not isinstance(outcome, dict):
            return _unknown("malformed_event")
        if signal.get("binding") != binding:
            return _unknown("binding_changed")
        if (signal.get("status") != "observed" or signal.get("signal_id") != "health"
                or outcome.get("status") != "SOFT_CHANGED"
                or outcome.get("signal_id") != "health"):
            return _unknown("invalid_soft_receipt")
        source_value = outcome.get("source_value")
        current_value = signal.get("value")
        age = outcome.get("source_age_ms")
        guard_id = outcome.get("guard_id")
        if (type(source_value) is not int or type(current_value) is not int
                or outcome.get("current_value") != current_value
                or type(age) not in (int, float) or not math.isfinite(age) or age < 0
                or not isinstance(guard_id, str) or len(guard_id) > 64):
            return _unknown("invalid_soft_receipt")
        previous_sequence = sequence

    latest = events[-1]
    signal = latest["signal"]
    outcome = latest["outcome"]
    return {
        "state": "OBSERVED", "sequence": latest["sequence"],
        "signal_id": "health", "source_value": outcome["source_value"],
        "current_value": signal["value"], "source_age_ms": outcome["source_age_ms"],
        "guard_id": outcome["guard_id"], "outcome": "SOFT_CHANGED",
        "soft_event_count": len(events), "grants_input_authority": False,
        "task_success_verified": False,
    }


def audit_packet(packet: dict) -> None:
    cases = packet.get("cases") if isinstance(packet, dict) else None
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise ValueError("case_set_incomplete")
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("malformed_case")
        case_id = case.get("case_id")
        if case_id not in EXPECTED_CASES or case_id in seen:
            raise ValueError("case_id_invalid_or_duplicate")
        seen.add(case_id)
        state = case.get("history_state")
        events = case.get("raw_events")
        if state == "none":
            expected = {"state": "NONE"} if events == [] else _unknown("none_with_events")
        elif state == "observed":
            expected = _derive_observed(case)
        elif state in {"invalidated", "unknown", "expired"}:
            expected = _unknown(state)
            if events != []:
                expected = _unknown("history_in_state_mismatch")
        else:
            expected = _unknown("history_state_unknown")

        actual = case.get("context")
        if actual != expected:
            raise ValueError(f"{case_id}: context_mismatch_latest_or_provenance")
        if actual.get("state") == "OBSERVED":
            if set(actual) != CONTEXT_KEYS:
                raise ValueError(f"{case_id}: context_schema_mismatch")
            if actual["grants_input_authority"] is not False or actual["task_success_verified"] is not False:
                raise ValueError(f"{case_id}: authority_or_success_expansion")
        expected_prompt = PROMPT_PREFIX + json.dumps(actual, sort_keys=True, separators=(",", ":")) + "\n"
        if case.get("prompt") != expected_prompt:
            raise ValueError(f"{case_id}: prompt_context_mismatch")
    if seen != EXPECTED_CASES:
        raise ValueError("case_set_incomplete")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: audit_soft_event_context_6561.py RAW_PACKET.json", file=sys.stderr)
        return 2
    try:
        packet = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        audit_packet(packet)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"FAIL_RAW_AUDIT: {exc}", file=sys.stderr)
        return 1
    print("PASS_RAW_AUDIT cases=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


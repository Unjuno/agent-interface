"""Deterministic, side-effect-free lifecycle adapter fixture for Issue #2309."""
from __future__ import annotations

from typing import Any, Iterable, Mapping

KNOWN = {
    "SETUP_DOCTOR", "OBSERVATION", "GUARDED_DISPATCH", "REFUSAL",
    "USEFUL_EFFECT", "STALE_INVALIDATION", "REPAIR", "TERMINAL_RELEASE",
    "CLEANUP_FAILURE",
}

def exchange(trace: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    attempts = []
    authority_grants = 0
    for index, event in enumerate(trace, 1):
        state = event.get("state")
        row = {
            "attempt": index,
            "state": state,
            "authority_granted": False,
            "task_success": False,
            "program_completed": False,
            "partial_effect": False,
            "release_attempted": False,
            "released": False,
        }
        if state not in KNOWN:
            row.update(status="unknown_rejected", reason="UNKNOWN_STATE_FAIL_CLOSED")
            attempts.append(row)
            continue
        if state == "SETUP_DOCTOR":
            row["status"] = "diagnostic"
        elif state == "OBSERVATION":
            row["status"] = "observed"
        elif state == "GUARDED_DISPATCH":
            row.update(status="guarded_dispatch", partial_effect=True)
        elif state == "REFUSAL":
            row.update(status="refused", reason=event.get("reason", "GUARD拒否"))
        elif state == "USEFUL_EFFECT":
            row.update(status="effect_recorded", partial_effect=True, task_success=True)
        elif state == "STALE_INVALIDATION":
            row.update(status="stale_invalidated", reason="FRESHNESS_LOST")
        elif state == "REPAIR":
            row.update(status="repair_recorded", partial_effect=True)
        elif state == "TERMINAL_RELEASE":
            row.update(status="released", release_attempted=True, released=True,
                       program_completed=True, task_success=True)
        elif state == "CLEANUP_FAILURE":
            row.update(status="cleanup_failed", reason="CLEANUP_ERROR",
                       release_attempted=True, released=False)
        attempts.append(row)
    return {
        "schema": "agent-interface/lifecycle-adapter-trace-v1",
        "attempts": attempts,
        "attempt_count": len(attempts),
        "authority_grants": authority_grants,
        "program_completed": any(row["program_completed"] for row in attempts),
        "task_success": any(row["task_success"] for row in attempts),
        "cleanup_failures": sum(row["status"] == "cleanup_failed" for row in attempts),
        "unknown_rejections": sum(row["status"] == "unknown_rejected" for row in attempts),
    }

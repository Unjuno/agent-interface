"""Static scope preflight for the #2678 integrated-route allocation.

This verifier never upgrades retained component evidence into route success.
"""
from __future__ import annotations
import json
from pathlib import Path

RESULT = Path("research/integration/golden_v3_orbstack_2558_six_allocation_v1/RESULT.json")
REQUIRED_OUTCOMES = {
    "effects", "visual_target_revalidation", "release_verified",
    "continuations_without_replay", "focus_change_refused",
    "focus_change_emissions_delta_zero",
}

def verify() -> dict:
    data = json.loads(RESULT.read_text(encoding="utf-8"))
    reasons = []
    if data.get("count") != 6:
        reasons.append("SIX_ALLOCATION_COUNT")
    if set(data.get("outcomes", {})) != REQUIRED_OUTCOMES:
        reasons.append("OUTCOME_COVERAGE")
    if data.get("authority_granted") is not False:
        reasons.append("AUTHORITY_NOT_FALSE")
    if data.get("full_preregistered_golden_comparison") is not True:
        reasons.append("FULL_PREREGISTERED_COMPARISON_MISSING")
    decision = "PASS_ROUTE_PRECONDITION" if not reasons else "HOLD_ROUTE_COVERAGE_INCOMPLETE"
    return {
        "schema": "golden-route-scope-preflight-2678-v1",
        "decision": decision,
        "source_result": str(RESULT).replace("\\", "/"),
        "reasons": reasons,
        "component_count": data.get("count"),
        "full_preregistered_golden_comparison": data.get("full_preregistered_golden_comparison"),
        "route_success_claim": False,
    }

if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))

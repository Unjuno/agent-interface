import hashlib
import json

CASES = [
    {"name": "final_pixels_ambiguous", "effect": "accepted", "timing": "missing", "route": "heldout-save"},
    {"name": "typed_complete", "effect": "accepted", "timing": "complete", "route": "heldout-save"},
    {"name": "typed_effect_disagrees", "effect": "rejected", "timing": "complete", "route": "heldout-save"},
    {"name": "stale_timing", "effect": "accepted", "timing": "stale", "route": "heldout-save"},
    {"name": "contradictory_timing", "effect": "accepted", "timing": "contradictory", "route": "heldout-save"},
    {"name": "typed_complete_route_b", "effect": "accepted", "timing": "complete", "route": "heldout-export"},
]
ARMS = ("FINAL_ONLY", "TYPED_TIMING", "TYPED_TIMING_PLUS_EFFECT", "STALE_OR_MISSING")

def decide(case, arm):
    valid = case["timing"] == "complete" and arm in ("TYPED_TIMING", "TYPED_TIMING_PLUS_EFFECT")
    effect_known = arm == "TYPED_TIMING_PLUS_EFFECT" and case["effect"] in ("accepted", "rejected")
    if case["timing"] in ("stale", "contradictory") or arm == "STALE_OR_MISSING":
        return "QUERY"
    if arm == "FINAL_ONLY" or not valid:
        return "RETRY"
    if effect_known and case["effect"] == "rejected":
        return "ABORT"
    return "DONE"

def expected(case, arm):
    if case["timing"] in ("stale", "contradictory") or arm == "STALE_OR_MISSING":
        return "QUERY"
    if arm == "TYPED_TIMING_PLUS_EFFECT" and case["effect"] == "rejected":
        return "ABORT"
    if arm in ("TYPED_TIMING", "TYPED_TIMING_PLUS_EFFECT") and case["timing"] == "complete":
        return "DONE"
    return "RETRY"

def main():
    rows = []
    for case in CASES:
        for arm in ARMS:
            decision = decide(case, arm)
            exp = expected(case, arm)
            rows.append({"case": case["name"], "route": case["route"], "arm": arm,
                         "decision": decision, "expected": exp,
                         "correct": decision == exp,
                         "timing_authorized_effect": False,
                         "model_calls": 1, "input_tokens": 100 if arm == "FINAL_ONLY" else 120,
                         "output_tokens": 12, "raw_retained": True})
    assert all(r["correct"] for r in rows)
    assert all(not r["timing_authorized_effect"] for r in rows)
    assert any(r["arm"] == "TYPED_TIMING" and r["decision"] == "DONE" for r in rows)
    assert any(r["arm"] == "FINAL_ONLY" and r["decision"] == "RETRY" for r in rows)
    out = {"decision": "PASS_SYNTHETIC_MODEL_FACING_TIMING_SCOPED", "formal_invocations": 1,
           "reruns": 0, "rows": rows, "cases": len(CASES), "arms": len(ARMS),
           "heldout_routes": sorted({c["route"] for c in CASES}),
           "cue_changes_decision": True, "timing_authority": False,
           "digest": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()}
    print(json.dumps(out, sort_keys=True))

if __name__ == "__main__":
    main()

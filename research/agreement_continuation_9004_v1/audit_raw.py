#!/usr/bin/env python3
"""Raw-only independent reconstruction; intentionally does not import candidate."""
import json
import sys
from pathlib import Path

ARMS = ("always_wait", "system1_only", "agreement_only", "agreement_lease")


def expected(case, arm, lease):
    invalid = case["revocation"] is not None
    if case["release_ok"] is False:
        return {"actions": [], "decision_ticks": [], "stop": "release_failure", "release_required": True,
                "release_ok": False, "effect_correct": True}
    if arm == "always_wait":
        valid = not invalid and case["s2"] == case["truth"]
        return {"actions": [case["s2"], case["s2"]] if valid else [],
                "decision_ticks": [case["s2_delay"], case["s2_delay"] + 1] if valid else [],
                "stop": "complete" if valid else "wait_or_gate", "release_required": True,
                "release_ok": True, "effect_correct": True}
    if arm == "system1_only":
        proposed = case["s1"][:lease["max_actions"]]
        kept = [] if invalid else [x for x in proposed if x == case["truth"]]
        return {"actions": kept, "decision_ticks": list(range(len(kept))),
                "stop": "revoked_or_gate" if invalid or len(kept) != len(proposed) else "complete",
                "release_required": True, "release_ok": True, "effect_correct": True}
    if invalid or case["agreement"] is not True:
        return {"actions": [], "decision_ticks": [], "stop": "yield", "release_required": True,
                "release_ok": True, "effect_correct": True}
    safe = lambda x: x == case["truth"] and x != "commit"
    if arm == "agreement_only":
        action = case["s1"][0]
        ok = safe(action)
        return {"actions": [action] if ok else [], "decision_ticks": [0] if ok else [],
                "stop": "complete" if ok else "independent_gate", "release_required": True,
                "release_ok": True, "effect_correct": True}
    proposals = case["s1"][:lease["max_actions"]]
    kept = []
    for tick, action in enumerate(proposals):
        if tick > lease["max_ticks"] or not safe(action):
            break
        kept.append((action, tick))
    return {"actions": [a for a, _ in kept], "decision_ticks": [t for _, t in kept],
            "stop": "complete" if len(kept) == lease["max_actions"] else "lease_or_independent_gate",
            "release_required": True, "release_ok": True, "effect_correct": True}


def audit(cases, raw):
    errors = []
    if raw.get("schema") != "agreement-continuation-raw-v1":
        errors.append("raw schema mismatch")
    if raw.get("claims") != {"live_actuation": False, "synthetic_timing": True}:
        errors.append("claim scope mismatch")
    index = {}
    for row in raw.get("rows", []):
        key = (row.get("case_id"), row.get("arm"))
        if key in index:
            errors.append(f"duplicate row {key}")
        index[key] = row
    expected_keys = {(c["id"], a) for c in cases["cases"] for a in ARMS}
    if set(index) != expected_keys:
        errors.append("coverage mismatch")
    for case in cases["cases"]:
        for arm in ARMS:
            row = index.get((case["id"], arm))
            if row is None:
                continue
            reconstructed = expected(case, arm, cases["lease"])
            observed = {k: row.get(k) for k in reconstructed}
            if observed != reconstructed:
                errors.append(f"transition/effect/release reconstruction mismatch {case['id']} {arm}")
            if any(a != case["truth"] for a in row.get("actions", [])):
                errors.append(f"unsafe task effect {case['id']} {arm}")
            if row.get("release_required") is not True:
                errors.append(f"release obligation missing {case['id']} {arm}")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
            "formal_pass": False, "live_actuation": False, "timing_claim": False,
            "cases": len(cases["cases"]), "rows": len(index), "errors": errors}


if __name__ == "__main__":
    case_path, raw_path, out_path = map(Path, sys.argv[1:4])
    result = audit(json.loads(case_path.read_text()), json.loads(raw_path.read_text()))
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])
    sys.exit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)

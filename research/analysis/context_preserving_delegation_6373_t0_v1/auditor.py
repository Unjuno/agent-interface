"""Independent declarative reconstruction; does not import candidate.py."""
import copy
import json
import sys

POLICIES = ("NO_RESTORE", "SUMMARY_ONLY", "RESTORE_ONLY", "RESTORE_PLUS_DIFF")


def state_diff(a, b):
    changed = {}
    for key in sorted(set(a) | set(b)):
        if a.get(key) != b.get(key):
            changed[key] = {"before": a.get(key), "after": b.get(key)}
    return changed


def expected_record(case, policy):
    state = dict(case["terminal"])
    effects = dict(case["effects_after"])
    restored = []
    if policy == "RESTORE_ONLY":
        restored = [f for f in case["restore_fields"] if f in case["initial"]]
    elif policy == "RESTORE_PLUS_DIFF":
        for field in case["restore_fields"]:
            independent = field not in case["external_fields"] + case["unknown_fields"]
            uncoupled = field not in case["restore_side_effects"]
            retains_evidence = not (field == "download" and state.get(field) in case["required_artifacts"])
            if independent and uncoupled and retains_evidence and field in case["initial"]:
                restored.append(field)
    for field in restored:
        state[field] = case["initial"][field]
        if policy == "RESTORE_ONLY":
            for effect, value in case["restore_side_effects"].get(field, {}).items():
                effects[effect] = value
    residual = state_diff(case["initial"], state) if policy in ("SUMMARY_ONLY", "RESTORE_PLUS_DIFF") else {}
    mismatches = sum(1 for key, value in case["next_requires"].items() if state.get(key) != value)
    lost_effect = any(effects.get(k) != v for k, v in case["effects_after"].items())
    lost_artifact = any(value not in state.values() for value in case["required_artifacts"])
    cleared_unknown = any(k in restored and state.get(k) == case["initial"].get(k) for k in case["unknown_fields"])
    return {"case":case["id"],"policy":policy,"context_after":state,"effects_after":effects,
            "restored_fields":sorted(restored),"residual_state_diff":residual,
            "modeled_context_mismatches":mismatches,"effects_lost":lost_effect,
            "external_overwrite":any(k in restored for k in case["external_fields"]),
            "artifacts_lost":lost_artifact,"unresolved_cleared":cleared_unknown}


def audit(fixture_path, oracle_path, candidate_path):
    cases = json.load(open(fixture_path, encoding="utf-8"))["cases"]
    oracle = json.load(open(oracle_path, encoding="utf-8"))["expected_case_safety"]
    observed = json.load(open(candidate_path, encoding="utf-8"))
    actual = {(r["case"],r["policy"]):r for r in observed}
    expected = [expected_record(c,p) for c in cases for p in POLICIES]
    rows = [{"case":e["case"],"policy":e["policy"],"matches":actual.get((e["case"],e["policy"]))==e} for e in expected]
    plus = [actual[(c["id"],"RESTORE_PLUS_DIFF")] for c in cases]
    summary = [actual[(c["id"],"SUMMARY_ONLY")] for c in cases]
    safety = {
        "effects_preserved": all(not r["effects_lost"] and r["effects_after"] == oracle[r["case"]] for r in plus),
        "external_fields_preserved": all(not r["external_overwrite"] for r in plus),
        "required_artifacts_preserved": all(not r["artifacts_lost"] for r in plus),
        "unknowns_not_cleared": all(not r["unresolved_cleared"] for r in plus),
        "residual_diff_exact": all(r["residual_state_diff"] == state_diff(next(c["initial"] for c in cases if c["id"]==r["case"]),r["context_after"]) for r in plus),
        "modeled_mismatches_reduced_vs_summary": sum(r["modeled_context_mismatches"] for r in plus) < sum(r["modeled_context_mismatches"] for r in summary),
    }
    return {"rows":len(rows),"rows_match":all(r["matches"] for r in rows),"safety":safety,
            "policy_totals":{p:sum(actual[(c["id"],p)]["modeled_context_mismatches"] for c in cases) for p in POLICIES},
            "restore_only_destructive_cases":[c["id"] for c in cases if actual[(c["id"],"RESTORE_ONLY")]["effects_lost"] or actual[(c["id"],"RESTORE_ONLY")]["external_overwrite"] or actual[(c["id"],"RESTORE_ONLY")]["artifacts_lost"] or actual[(c["id"],"RESTORE_ONLY")]["unresolved_cleared"]],
            "decision":"PASS_METHOD_SCOPED" if all(r["matches"] for r in rows) and all(safety.values()) else "FAIL_OR_UNCERTAIN"}


if __name__ == "__main__":
    print(json.dumps(audit(*sys.argv[1:]),sort_keys=True,separators=(",",":")))

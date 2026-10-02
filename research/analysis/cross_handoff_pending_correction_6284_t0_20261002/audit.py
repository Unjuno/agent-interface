"""Independent transition-table reconstruction for the frozen #6284 fixture."""
import json
import sys


def canon(key, aliases):
    trail = []
    while key in aliases and key not in trail:
        trail.append(key)
        key = aliases[key]
    return key


def expected_case(case):
    policy_rows = {}
    for policy in ("visible_state_only", "typed_handoff", "correction_conservation", "retry_plus_obligation_ledger"):
        outstanding = {}
        intent_ops = set()
        trace = []
        for step in case["operations"]:
            kind = step["op"]
            if kind == "issue":
                same_intent = (step["intent"], step["effect_key"]) in intent_ops
                unresolved = [x for x in outstanding.values() if not x["done"]]
                conflict = any(canon(x["resource"], case["alias"]) == canon(step["resource"], case["alias"])
                               or (policy == "correction_conservation" and x["goal"] == step["goal"] and x["key"] == step["effect_key"])
                               for x in unresolved)
                unknown = bool(unresolved) and (not case["footprints_complete"] or step["resource"] == "unknown")
                if same_intent:
                    result = "REJECT_DUPLICATE_INTENT"
                elif policy in ("correction_conservation", "retry_plus_obligation_ledger") and unknown:
                    result = "HOLD_UNKNOWN_FOOTPRINT"
                elif policy in ("correction_conservation", "retry_plus_obligation_ledger") and conflict:
                    result = "HOLD_PENDING_OVERLAP"
                else:
                    result = "ISSUED"
                trace.append({"policy": policy, "operation": step["operation"], "intent": step["intent"],
                              "status": result, "permitted": result == "ISSUED"})
                if result == "ISSUED":
                    outstanding[step["operation"]] = {"goal": step["goal"], "key": step["effect_key"],
                                                       "resource": step["resource"], "done": False}
                    intent_ops.add((step["intent"], step["effect_key"]))
            elif kind == "release":
                trace.append({"policy": policy, "operation": step["operation"],
                              "status": "SAFETY_RELEASE_BYPASS", "permitted": True})
                outstanding[step["operation"]] = {"goal": step["goal"], "key": step["effect_key"],
                                                   "resource": step["resource"], "done": False}
            elif kind == "effect" and step["operation"] in outstanding:
                outstanding[step["operation"]]["done"] = step["effect"] != "partial"
                trace.append({"policy": policy, "operation": step["operation"],
                              "status": "OBSERVED_" + step["effect"], "time": step["time"]})
        policy_rows[policy] = {"decisions": trace,
                               "admitted": [r["operation"] for r in trace if r.get("status") == "ISSUED"],
                               "unresolved_at_end": sorted(k for k, v in outstanding.items() if not v["done"])}
    return policy_rows


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    candidate = json.load(sys.stdin)
    expected = {case["id"]: expected_case(case) for case in fixture["cases"]}
    if candidate != expected:
        raise SystemExit("independent transition reconstruction mismatch")
    required = {"delayed_same_resource_new_intent", "late_effect_after_handoff_partial_then_duplicate",
                "dedupe-expired-new-intent", "semantic_overlap_unknown_footprint",
                "distinct_goal_and_safety_release", "resource_alias_complete_footprint"}
    if set(candidate) != required:
        raise SystemExit("frozen case set mismatch")
    for name in ("delayed_same_resource_new_intent", "late_effect_after_handoff_partial_then_duplicate",
                 "dedupe-expired-new-intent", "resource_alias_complete_footprint"):
        if len(candidate[name]["visible_state_only"]["admitted"]) < 2:
            raise SystemExit("positive duplicate-proposal control absent: " + name)
        if len(candidate[name]["retry_plus_obligation_ledger"]["admitted"]) != 1:
            raise SystemExit("D baseline failed to block overlapping new intent: " + name)
    unknown = candidate["semantic_overlap_unknown_footprint"]["retry_plus_obligation_ledger"]["decisions"]
    if not any(x["status"] == "HOLD_UNKNOWN_FOOTPRINT" for x in unknown):
        raise SystemExit("unknown footprint did not HOLD")
    release = candidate["distinct_goal_and_safety_release"]["retry_plus_obligation_ledger"]["decisions"]
    if not any(x["status"] == "SAFETY_RELEASE_BYPASS" and x["permitted"] for x in release):
        raise SystemExit("safety release was suppressed")
    print(json.dumps({"audit": "PASS_METHOD_SCOPED", "cases": len(candidate),
                      "policy_reconstructions": sum(len(x) for x in candidate.values()),
                      "D_subsumption_cases": 4, "errors": []}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

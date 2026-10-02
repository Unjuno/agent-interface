"""Finite-policy comparator for Issue #6284's pending-correction discriminator."""
import json
import sys


def root(name, aliases):
    seen = set()
    while name in aliases and name not in seen:
        seen.add(name)
        name = aliases[name]
    return name


def run(case):
    results = {}
    for policy in ("visible_state_only", "typed_handoff", "correction_conservation", "retry_plus_obligation_ledger"):
        pending, issued, rows = {}, [], []
        for event in case["operations"]:
            op = event["op"]
            if op == "issue":
                active = [v for v in pending.values() if not v["resolved"]]
                repeated_id = any(v["intent"] == event["intent"] and v["effect_key"] == event["effect_key"]
                                  for v in issued)
                if repeated_id:
                    status = "REJECT_DUPLICATE_INTENT"
                elif policy in ("correction_conservation", "retry_plus_obligation_ledger") and active and (not case["footprints_complete"] or event["resource"] == "unknown"):
                    status = "HOLD_UNKNOWN_FOOTPRINT"
                elif policy in ("correction_conservation", "retry_plus_obligation_ledger") and any(root(v["resource"], case["alias"]) == root(event["resource"], case["alias"]) for v in active):
                    status = "HOLD_PENDING_OVERLAP"
                elif policy == "correction_conservation" and active and any(v["goal"] == event["goal"] and v["effect_key"] == event["effect_key"] for v in active):
                    status = "HOLD_SEMANTIC_OVERLAP"
                else:
                    status = "ISSUED"
                permitted = status == "ISSUED"
                rows.append({"policy": policy, "operation": event["operation"], "intent": event["intent"],
                             "status": status, "permitted": permitted})
                if permitted:
                    pending[event["operation"]] = {"intent": event["intent"], "goal": event["goal"],
                                                    "effect_key": event["effect_key"], "resource": event["resource"],
                                                    "resolved": False}
                    issued.append(event)
            elif op == "release":
                rows.append({"policy": policy, "operation": event["operation"], "status": "SAFETY_RELEASE_BYPASS", "permitted": True})
                pending[event["operation"]] = {"intent": None, "goal": event["goal"], "effect_key": event["effect_key"],
                                                "resource": event["resource"], "resolved": False}
            elif op == "effect" and event["operation"] in pending:
                pending[event["operation"]]["resolved"] = event["effect"] != "partial"
                rows.append({"policy": policy, "operation": event["operation"], "status": "OBSERVED_" + event["effect"], "time": event["time"]})
        results[policy] = {"decisions": rows, "admitted": [e["operation"] for e in issued],
                           "unresolved_at_end": sorted(k for k, v in pending.items() if not v["resolved"])}
    return results


def main():
    fixture = json.load(sys.stdin)
    print(json.dumps({case["id"]: run(case) for case in fixture["cases"]}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

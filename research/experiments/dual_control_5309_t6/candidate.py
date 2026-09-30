"""Finite T6 dual-control fallback experiment for Issue #5309.

This is a synthetic policy-boundary model. It deliberately gives no authority
to the probe or scorer and enumerates the full finite input product.
"""
import hashlib
import itertools
import json


def decide(target, probe_state, probe_cost, harm, budget, fallback):
    if probe_state != "VALID":
        return "YIELD" if fallback == "YIELD" else "TASK_ACTION"
    if harm > budget:
        return "YIELD"
    if probe_cost > 1:
        return "TASK_ACTION"
    return "PROBE"


def score(decision, target, probe_state, harm, budget):
    """Independent outcome scorer over hidden target/effect fields."""
    if decision == "PROBE":
        return {"wrong_target": False, "effect": "NONE", "authority": False}
    if decision == "TASK_ACTION":
        return {
            "wrong_target": target != "A",
            "effect": "COMMIT_A",
            "authority": False,
        }
    return {"wrong_target": False, "effect": "NONE", "authority": False}


def main():
    rows = []
    for target, state, cost, harm, budget, fallback in itertools.product(
        ("A", "B"), ("VALID", "FAILED", "UNKNOWN", "STALE"),
        (0, 1, 2), (0, 1, 2), (0, 1, 2), ("YIELD", "TASK"),
    ):
        decision = decide(target, state, cost, harm, budget, fallback)
        observed = score(decision, target, state, harm, budget)
        rows.append({
            "target": target, "probe_state": state, "probe_cost": cost,
            "harm": harm, "budget": budget, "fallback": fallback,
            "decision": decision, **observed,
        })
    assert len(rows) == 2 * 4 * 3 * 3 * 3 * 2 == 432
    assert all(not r["authority"] for r in rows)
    assert all(r["decision"] != "PROBE" for r in rows if r["probe_state"] != "VALID")
    assert all(r["decision"] != "PROBE" for r in rows if r["harm"] > r["budget"])
    assert all(r["decision"] != "PROBE" for r in rows if r["probe_cost"] > 1)
    failed_task = [r for r in rows if r["probe_state"] == "FAILED" and r["decision"] == "TASK_ACTION"]
    failed_yield = [r for r in rows if r["probe_state"] == "FAILED" and r["decision"] == "YIELD"]
    assert len(failed_task) == len(failed_yield) == 54
    assert sum(r["wrong_target"] for r in failed_task) == 27
    assert sum(r["wrong_target"] for r in failed_yield) == 0
    payload = {
        "experiment": "issue-5309-t6-probe-failure-fallback",
        "scope": "synthetic finite policy model; no live authority or GUI effects",
        "case_count": len(rows),
        "assertions": 8,
        "failed_probe_task_fallback": {
            "rows": len(failed_task),
            "wrong_target": sum(r["wrong_target"] for r in failed_task),
        },
        "failed_probe_yield_fallback": {
            "rows": len(failed_yield),
            "wrong_target": sum(r["wrong_target"] for r in failed_yield),
        },
        "all_rows": rows,
    }
    semantic = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["semantic_sha256"] = hashlib.sha256(semantic.encode()).hexdigest()
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

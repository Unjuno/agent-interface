import itertools
import json
from pathlib import Path


def bounds_at(case, tick):
    return case.get("safe_by_tick", {}).get(str(tick), case["safe"])


def enumerate_tube(case, disturbances, action, hold, release_lag):
    lo, hi = case["initial"]
    states = {x: [x] for x in range(lo, hi + 1)}
    rows = [{"tick": 0, "states": sorted(states)}]
    for tick in range(1, hold + release_lag + 1):
        commanded = action if tick <= hold else 0
        nxt = {}
        for x, path in states.items():
            for w in disturbances:
                y = x + commanded + w
                nxt.setdefault(y, path + [y])
        states = nxt
        rows.append({"tick": tick, "states": sorted(states)})
    safe = all(all(bounds_at(case, row["tick"])[0] <= x <= bounds_at(case, row["tick"])[1] for x in row["states"]) for row in rows)
    return {"safe": safe, "prefixes": rows}


def evaluate_case(case, data):
    hmax, act, dist = data["max_horizon"], case.get("action", data["action"]), case.get("disturbances", data["disturbances"])
    lag = case["release_lag"]
    if not case["model_valid"]:
        return {"id": case["id"], "disposition": "YIELD_MODEL_INVALID", "policies": {}}
    if not case["target_valid"]:
        return {"id": case["id"], "disposition": "YIELD_TARGET_INVALID", "policies": {}}
    robust_admitted = [h for h in range(1, hmax + 1) if enumerate_tube(case, dist, act, h, lag)["safe"]]
    nominal_admitted = [h for h in range(1, hmax + 1) if enumerate_tube(case, [0], act, h, lag)["safe"]]
    policies = {}
    for name, requested, model_dist in (
        ("FIXED_SHORT", 1, dist), ("FIXED_LONG", hmax, dist),
        ("NOMINAL_POINT", max(nominal_admitted, default=0), [0]),
        ("ROBUST_TUBE", max(robust_admitted, default=0), dist),
    ):
        if requested == 0:
            policies[name] = {"decision": "YIELD", "requested_horizon": 0, "horizon": 0, "observations": 0, "useful_displacement": 0, "model_tube_safe": False, "actual_gate_safe": False, "tube": [], "release_tick": None}
            continue
        tube = enumerate_tube(case, model_dist, act, requested, lag)
        # Even nominal and fixed policies are subject to the same actual robust admission gate.
        admitted = enumerate_tube(case, dist, act, requested, lag)["safe"]
        policies[name] = {
            "decision": "ADMIT" if admitted else "YIELD",
            "requested_horizon": requested,
            "horizon": requested if admitted else 0,
            "observations": 1 if admitted else 0,
            "useful_displacement": requested * act if admitted else 0,
            "model_tube_safe": tube["safe"],
            "actual_gate_safe": admitted,
            "tube": tube["prefixes"] if admitted else [],
            "release_tick": requested + lag if admitted else None,
        }
    return {"id": case["id"], "disposition": "EVALUATED", "policies": policies}


def run(data):
    return {"allocation_id": data["allocation_id"], "results": [evaluate_case(c, data) for c in data["cases"]]}


def main():
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--input", required=True); p.add_argument("--output", required=True); a = p.parse_args()
    result = run(json.loads(Path(a.input).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"evaluated {len(result['results'])} frozen cases")


if __name__ == "__main__": main()

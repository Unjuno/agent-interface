import itertools
import json
from pathlib import Path


def brute_tube(case, disturbances, action, hold, lag):
    paths = [[x] for x in range(case["initial"][0], case["initial"][1] + 1)]
    all_rows = [{"tick": 0, "states": sorted(p[0] for p in paths)}]
    for t in range(1, hold + lag + 1):
        u = action if t <= hold else 0
        paths = [p + [p[-1] + u + w] for p in paths for w in disturbances]
        all_rows.append({"tick": t, "states": sorted({p[-1] for p in paths})})
    safe = True
    for row in all_rows:
        lo, hi = case.get("safe_by_tick", {}).get(str(row["tick"]), case["safe"])
        if any(x < lo or x > hi for x in row["states"]): safe = False
    return safe, all_rows


def audit(data, candidate):
    errors = []
    if candidate.get("allocation_id") != data["allocation_id"]: errors.append("allocation_binding")
    if len(candidate.get("results", [])) != len(data["cases"]): errors.append("case_count")
    summary = []
    for case, row in zip(data["cases"], candidate.get("results", [])):
        if row.get("id") != case["id"]: errors.append("case_order_or_id:" + case["id"]); continue
        if not case["model_valid"] or not case["target_valid"]:
            want = "YIELD_MODEL_INVALID" if not case["model_valid"] else "YIELD_TARGET_INVALID"
            if row.get("disposition") != want or row.get("policies") != {}: errors.append("invalidation:" + case["id"])
            continue
        action = case.get("action", data["action"])
        disturbances = case.get("disturbances", data["disturbances"])
        robust = []
        for h in range(1, data["max_horizon"] + 1):
            safe, _ = brute_tube(case, disturbances, action, h, case["release_lag"])
            if safe: robust.append(h)
        expected_robust = max(robust, default=0)
        policies = row.get("policies", {})
        polsum = {}
        for name, requested, modeldist in (
            ("FIXED_SHORT",1,disturbances), ("FIXED_LONG",data["max_horizon"],disturbances),
            ("NOMINAL_POINT",None,[0]), ("ROBUST_TUBE",expected_robust,disturbances),
        ):
            p = policies.get(name, {})
            if name == "NOMINAL_POINT":
                admissible = [h for h in range(1,data["max_horizon"]+1) if brute_tube(case,[0],action,h,case["release_lag"])[0]]
                requested = max(admissible,default=0)
            gate = requested > 0 and brute_tube(case,disturbances,action,requested,case["release_lag"])[0]
            if p.get("decision") != ("ADMIT" if gate else "YIELD") or p.get("horizon") != (requested if gate else 0): errors.append(f"gate:{case['id']}:{name}")
            nominal_safe, _ = brute_tube(case, modeldist, action, requested, case["release_lag"]) if requested else (False, [])
            if p.get("model_tube_safe") != nominal_safe or p.get("actual_gate_safe") != gate: errors.append(f"model_vs_gate:{case['id']}:{name}")
            if gate:
                safe, rows = brute_tube(case,modeldist,action,requested,case["release_lag"])
                if p.get("tube") != rows: errors.append(f"tube_coverage:{case['id']}:{name}")
                if p.get("release_tick") != requested + case["release_lag"]: errors.append(f"release:{case['id']}:{name}")
                if p.get("observations") != 1 or p.get("useful_displacement") != requested * action: errors.append(f"accounting:{case['id']}:{name}")
            elif p.get("tube") != [] or p.get("observations") != 0 or p.get("useful_displacement") != 0: errors.append(f"refusal_accounting:{case['id']}:{name}")
            polsum[name] = p.get("horizon")
        if polsum.get("ROBUST_TUBE") != expected_robust: errors.append("not_largest_safe_horizon:" + case["id"])
        summary.append({"id":case["id"],"robust_horizon":expected_robust,"policies":polsum})
    stress = data["stress"]
    x = stress["initial"][0]
    stress_path = [x]
    for _ in range(data["max_horizon"] + stress["release_lag"]):
        x += (data["action"] if len(stress_path) <= data["max_horizon"] else 0) + stress["disturbance"]
        stress_path.append(x)
    out_of_bound = next((x for x in stress_path if not stress["safe"][0] <= x <= stress["safe"][1]), None)
    stress_detected = out_of_bound is not None
    # The out-of-bound disturbance is a distinct stress trajectory, not an in-bound safety guarantee.
    if not stress_detected: errors.append("stress_control_not_outside_safe_set")
    return {"disposition":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "errors":errors,"summary":summary,"out_of_bound_stress_first_unsafe_state":out_of_bound,"out_of_bound_stress_path":stress_path,"stress_is_outside_model_assumption":stress_detected}


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);p.add_argument("--candidate",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    result=audit(json.loads(Path(a.input).read_text(encoding="utf-8")),json.loads(Path(a.candidate).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"disposition":result["disposition"],"errors":result["errors"]},sort_keys=True))
    return 0 if result["disposition"]=="PASS_METHOD_SCOPED" else 1


if __name__=="__main__": raise SystemExit(main())

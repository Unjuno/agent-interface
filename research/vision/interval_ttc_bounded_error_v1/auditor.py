"""Independent raw-only auditor; intentionally does not import candidate/generator."""
import hashlib
import json
import math
import sys
from collections import defaultdict

THRESHOLD = 2.0
MAX_LEAD_LOSS = 0.100


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def independently_estimate(history):
    if any(not math.isfinite(o["t_s"]) for o in history) or any(
            history[i]["t_s"] >= history[i + 1]["t_s"] for i in range(len(history) - 1)):
        return [(None, None) for _ in history]
    if any(history[i]["radius_px"] is None and history[i + 1]["radius_px"] is None
           for i in range(len(history) - 1)):
        return [(None, None) for _ in history]
    result = []
    for stop in range(1, len(history) + 1):
        prefix = [o for o in history[:stop] if o["radius_px"] is not None]
        if len(prefix) < 2:
            result.append((None, None)); continue
        if len({o["track_id"] for o in prefix}) != 1:
            result.append((None, None)); continue
        bounds = []
        bad = False
        for left, right in zip(prefix[:-1], prefix[1:]):
            dtime = right["t_s"] - left["t_s"]
            if dtime <= 0 or left["radius_px"] <= left["bound_px"] or right["radius_px"] <= right["bound_px"]:
                bad = True; break
            low_speed = ((right["radius_px"] - right["bound_px"]) - (left["radius_px"] + left["bound_px"])) / dtime
            high_speed = ((right["radius_px"] + right["bound_px"]) - (left["radius_px"] - left["bound_px"])) / dtime
            bounds.append((low_speed, high_speed))
        if bad or not bounds:
            result.append((None, None)); continue
        speed_floor = max(pair[0] for pair in bounds)
        speed_ceil = min(pair[1] for pair in bounds)
        if speed_floor <= 0 or speed_ceil < speed_floor:
            result.append((None, None)); continue
        last = prefix[-1]
        interval = ((last["radius_px"] - last["bound_px"]) / speed_ceil,
                    (last["radius_px"] + last["bound_px"]) / speed_floor)
        left, right = prefix[-2:]
        nominal_speed = (right["radius_px"] - left["radius_px"]) / (right["t_s"] - left["t_s"])
        point = right["radius_px"] / nominal_speed if nominal_speed > 0 else None
        result.append((point, interval))
    return result


def integrity_errors(public, oracle, candidate):
    pub = {x["id"]: x for x in public}; tru = {x["id"]: x for x in oracle}; cand = {x["id"]: x for x in candidate}
    errors = []
    if len(public) != 200 or len(oracle) != 200 or len(candidate) != 200 or set(pub) != set(tru) or set(pub) != set(cand):
        errors.append("row_count_or_ids")
    profile_counts = defaultdict(lambda: {"n":0,"hazard":0,"cal_hazard":0,"cal_control":0,"eval_hazard":0,"eval_control":0})
    for item in oracle:
        c = profile_counts[item["profile"]]; c["n"] += 1; c["hazard"] += bool(item["hazard"])
        c[("cal_" if item["split"] == "calibration" else "eval_") + ("hazard" if item["hazard"] else "control")] += 1
        if item["id"] in pub:
            expected_truth = item["truth"]
            if len(expected_truth) != len(pub[item["id"]]["history"]): errors.append("oracle_length:"+item["id"])
            else:
                for i,(a,b) in enumerate(zip(expected_truth,pub[item["id"]]["history"])):
                    if a["t_s"] != b["t_s"] or a["observed"] != (b["radius_px"] is not None):
                        errors.append(f"public_oracle_mismatch:{item['id']}:{i}")
                        break
    if len(profile_counts) != 10 or any(c["n"] != 20 or c["hazard"] != 10 or c["cal_hazard"] != 5 or c["cal_control"] != 5 or c["eval_hazard"] != 5 or c["eval_control"] != 5 for c in profile_counts.values()):
        errors.append("oracle_label_split_integrity")
    for sid, row in pub.items():
        expected = independently_estimate(row["history"])
        actual = cand.get(sid, {}).get("estimates", [])
        if len(actual) != len(expected):
            errors.append("prefix_count:" + sid); continue
        for i, ((point, interval), got) in enumerate(zip(expected, actual)):
            if point is None:
                if got["point_ttc_s"] is not None: errors.append(f"point_mismatch:{sid}:{i}")
            elif got["point_ttc_s"] is None or not math.isclose(point, got["point_ttc_s"], rel_tol=1e-10, abs_tol=1e-10):
                errors.append(f"point_mismatch:{sid}:{i}")
            if interval is None:
                if got["interval_s"] is not None: errors.append(f"interval_mismatch:{sid}:{i}")
            elif got["interval_s"] is None or not all(math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10) for a,b in zip(interval,got["interval_s"])):
                errors.append(f"interval_mismatch:{sid}:{i}")
            history = row["history"][:i+1]
            valid = [x for x in history if x["radius_px"] is not None]
            px = area = None
            if len(valid) >= 2 and valid[-2]["radius_px"] > 0 and valid[-1]["radius_px"] > 0:
                r0,r1=valid[-2]["radius_px"],valid[-1]["radius_px"]
                px,area=abs(r1-r0),abs((r1*r1)/(r0*r0)-1.0)
            if ((px is None) != (got.get("pixel_change_px") is None) or
                (px is not None and not math.isclose(px,got["pixel_change_px"],rel_tol=1e-10,abs_tol=1e-10)) or
                (area is None) != (got.get("relative_area_change") is None) or
                (area is not None and not math.isclose(area,got["relative_area_change"],rel_tol=1e-10,abs_tol=1e-10))):
                errors.append(f"simple_cue_mismatch:{sid}:{i}")
    return errors


def calibration_thresholds(predictions, oracle):
    truth = {x["id"]: x for x in oracle}
    thresholds = {}
    for method in ("point", "interval"):
        controls = [p for p in predictions if truth[p["id"]]["split"] == "calibration"
                    and not truth[p["id"]]["hazard"]]
        values = [2.0]
        for p in controls:
            for e in p["estimates"]:
                val = e["point_ttc_s"] if method == "point" else (e["interval_s"][1] if e["interval_s"] else None)
                if val is not None:
                    values.append(val)
        valid = []
        for threshold in sorted(set(values), reverse=True):
            false = 0
            for p in controls:
                if any((e["point_ttc_s"] is not None and e["point_ttc_s"] <= threshold)
                       if method == "point" else
                       (e["interval_s"] is not None and e["interval_s"][1] <= threshold)
                       for e in p["estimates"]):
                    false += 1
            if false == 0:
                valid.append(threshold)
        thresholds[method] = max(valid) if valid else 0.0
    for name, field, grid in (("pixel", "pixel_change_px", [50,100,200,400,800,1600,3200,6400,12800]),
                              ("area", "relative_area_change", [.01,.02,.05,.10,.20,.40,.80])):
        controls=[p for p in predictions if truth[p["id"]]["split"]=="calibration" and not truth[p["id"]]["hazard"]]
        valid=[]
        for threshold in grid:
            false=sum(any(e.get(field) is not None and e[field]>=threshold for e in p["estimates"]) for p in controls)
            if false==0: valid.append(threshold)
        thresholds[name]=max(valid) if valid else None
    return thresholds


def main(public_path, oracle_path, candidate_path, report_path):
    public, oracle, candidate = map(read_jsonl, (public_path, oracle_path, candidate_path))
    pub = {x["id"]: x for x in public}; tru = {x["id"]: x for x in oracle}; cand = {x["id"]: x for x in candidate}
    errors = integrity_errors(public, oracle, candidate)
    thresholds = calibration_thresholds(candidate, oracle)
    profile_stats = defaultdict(lambda: {"rows":0,"point_false_yield":0,"interval_false_yield":0,
                                         "point_hazard_yield":0,"interval_hazard_yield":0,
                                         "eligible_point_yield":0,"eligible_interval_yield":0,
                                         "eligible_prefixes":0,"eligible_numeric_intervals":0,
                                         "in_model_containment_misses":0,"fail_closed_yields":0})
    lead_failures = []
    for sid, truth in tru.items():
        if sid not in cand: continue
        p = cand[sid]; stats = profile_stats[truth["profile"]]; stats["rows"] += 1
        first = {"point":None,"interval":None}
        for i, e in enumerate(p["estimates"]):
            pv, iv = e["point_ttc_s"], e["interval_s"]
            if pv is not None and pv <= thresholds["point"] and first["point"] is None: first["point"] = i
            if iv is not None and iv[1] <= thresholds["interval"] and first["interval"] is None: first["interval"] = i
            if truth["eligible_in_model"] and truth["truth"][i]["observed"] and iv:
                true_ttc = truth["truth"][i]["true_ttc_s"]
                if true_ttc is not None and not (iv[0] - 1e-9 <= true_ttc <= iv[1] + 1e-9):
                    stats["in_model_containment_misses"] += 1
            if truth["eligible_in_model"] and truth["truth"][i]["observed"]:
                stats["eligible_prefixes"] += 1
                stats["eligible_numeric_intervals"] += iv is not None
            if i == len(p["estimates"])-1 and truth["profile"] in (
                    "identity_swap", "passby", "stationary", "acceleration", "occlusion", "understated_bound") \
                    and iv and iv[1] <= thresholds["interval"]:
                stats["fail_closed_yields"] += 1
        if truth["split"] == "evaluation":
            if not truth["hazard"]:
                stats["point_false_yield"] += first["point"] is not None
                stats["interval_false_yield"] += first["interval"] is not None
            else:
                stats["point_hazard_yield"] += first["point"] is not None
                stats["interval_hazard_yield"] += first["interval"] is not None
                if truth["eligible_in_model"]:
                    stats["eligible_point_yield"] += first["point"] is not None
                    stats["eligible_interval_yield"] += first["interval"] is not None
            if truth["hazard"] and truth["eligible_in_model"] and first["point"] is not None:
                ttc = truth["truth"][first["interval"]]["true_ttc_s"] if first["interval"] is not None else None
                point_ttc = truth["truth"][first["point"]]["true_ttc_s"]
                # Lead = TTC at cue. Later interval cue loses lead; missing cue is a failure.
                if ttc is None or point_ttc - ttc > MAX_LEAD_LOSS + 1e-9:
                    lead_failures.append(sid)
    errors.extend("calibration_false_budget:" + method for method in thresholds if thresholds[method] < 0)
    by_profile = {k: dict(v) for k,v in sorted(profile_stats.items())}
    mutation_checks = {}
    for name, mut in (("bound", lambda p,o,c: p[0]["history"][0].__setitem__("bound_px", 9.0)),
                      ("timestamp", lambda p,o,c: p[0]["history"][1].__setitem__("t_s", -5.0)),
                      ("sample", lambda p,o,c: p[0]["history"].pop()),
                      ("oracle_label", lambda p,o,c: o[0].__setitem__("hazard", not o[0]["hazard"])),
                      ("interval_endpoint", lambda p,o,c: c[0]["estimates"][1].__setitem__("interval_s", [0.0, 0.0]))):
        mp=json.loads(json.dumps(public)); mo=json.loads(json.dumps(oracle)); mc=json.loads(json.dumps(candidate))
        mut(mp,mo,mc)
        mutation_checks[name] = bool(integrity_errors(mp,mo,mc))
    noisy = ["iid", "correlated"]
    irregular = ["irregular_dropout"]
    strict_improvement = all(
        by_profile.get(profile, {}).get("interval_false_yield",0)
        < by_profile.get(profile, {}).get("point_false_yield",0)
        for profile in noisy + irregular)
    checks = {
        "rows_200": len(public) == 200 and len(oracle) == 200 and len(candidate) == 200,
        "calibration_controls_50": sum(x["split"] == "calibration" and not x["hazard"] for x in oracle) == 50,
        "evaluation_controls_50": sum(x["split"] == "evaluation" and not x["hazard"] for x in oracle) == 50,
        "candidate_reconstruction": not errors,
        "all_in_model_contained": all(x["in_model_containment_misses"] == 0 for x in by_profile.values()),
        "lead_criterion": not lead_failures,
        "eligible_hazard_yield": any(v["eligible_point_yield"] for v in by_profile.values()) and any(v["eligible_interval_yield"] for v in by_profile.values()),
        "in_model_interval_coverage": all(
            by_profile.get(p,{}).get("eligible_prefixes",0)>0 and
            by_profile[p]["eligible_numeric_intervals"] / by_profile[p]["eligible_prefixes"] >= 0.5
            for p in ("approach","iid","correlated","irregular_dropout")),
        "invalid_terminal_fail_closed": all(by_profile.get(p,{}).get("fail_closed_yields",0)==0 for p in
                                              ("passby","stationary","acceleration","occlusion","identity_swap","understated_bound")),
        "mutation_audit": all(mutation_checks.values()),
        "strict_false_yield_improvement": strict_improvement,
    }
    report = {"thresholds": thresholds, "profiles": by_profile,
              "lead_failures": lead_failures, "errors": errors,
              "mutation_checks": mutation_checks, "checks": checks,
        "decision": ("FAIL_METHOD" if errors or not checks["all_in_model_contained"]
                           or not checks["invalid_terminal_fail_closed"] or not checks["mutation_audit"] else
                           "PASS_METHOD_SCOPED" if checks["lead_criterion"] and checks["eligible_hazard_yield"]
                           and checks["in_model_interval_coverage"] and checks["strict_false_yield_improvement"]
                           else "NO_INCREMENTAL_VALUE")}
    with open(report_path,"w",encoding="utf-8") as f: json.dump(report,f,sort_keys=True,indent=2)
    if errors: return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))

"""Raw-only auditor for Issue #8597's finite synthetic ranking fixture."""
import argparse
import copy
import json
import math
from pathlib import Path

EXPECTED_PRIMARY = {
    "A": {"pooled_mean": 0.5, "es20": 2.2, "macro_mean": 0.5, "macro_es20": 1.3333333333333333},
    "B": {"pooled_mean": 0.5, "es20": 1.0, "macro_mean": 0.5, "macro_es20": 0.5},
}


def _es20(values):
    if not values:
        return None
    k = math.ceil(0.20 * len(values))
    return sum(sorted(values, reverse=True)[:k]) / k


def audit_payload(visible, truth, raw, run_mutations=True):
    errors = []
    source_ops = {o["opportunity_id"]: o for o in visible.get("assigned_opportunities", [])}
    expected_keys = set()
    observed = {}
    for row in raw.get("rows", []):
        key = (row.get("opportunity_id"), row.get("route"), row.get("tick"))
        if key in observed:
            errors.append(f"duplicate raw row {key}")
        observed[key] = row
    derived = {r: {} for r in visible.get("routes", [])}
    meta = {}
    target = truth.get("target_state_by_tick", {})
    hard_events = set(tuple(x) for x in truth.get("hard_safety_violations", []))
    for oid, opportunity in source_ops.items():
        meta[oid] = {"stratum": opportunity["stratum"], "cluster": opportunity["cluster"]}
        per_route = {r: [] for r in visible["routes"]}
        for tick in opportunity.get("ticks", []):
            key = (oid, tick["route"], tick["tick"])
            expected_keys.add(key)
            row = observed.get(key)
            expected_row = {"opportunity_id": oid, "stratum": opportunity["stratum"], "cluster": opportunity["cluster"], **tick}
            if row != expected_row:
                errors.append(f"raw/input mismatch {key}")
            state = target.get(oid, {}).get(tick["route"], {}).get(str(tick["tick"]))
            action = tick.get("selected_action")
            actions = tick.get("admissible_actions")
            if (oid, tick["route"], tick["tick"]) in hard_events or action not in actions:
                errors.append(f"hard safety violation {key}")
                continue
            if tick.get("opportunity_open") is not True:
                continue
            if state not in ("A", "B"):
                errors.append(f"missing truth inside scored cohort {key}")
                continue
            if not isinstance(actions, list) or not actions:
                errors.append(f"invalid admissible action set {key}")
                continue
            loss = {a: int(a != state) for a in actions}
            regret = loss[action] - min(loss.values())
            per_route[tick["route"]].append(regret)
        for route, losses in per_route.items():
            if len(losses) != 4:
                errors.append(f"incomplete four-tick opportunity {oid}/{route}")
            derived[route][oid] = sum(losses) if len(losses) == 4 else None
    if set(observed) != expected_keys:
        errors.append("raw key set differs from complete finite grid")
    if set(source_ops) != {f"{s}-O{i:02d}" for s in ("S1", "S2") for i in range(1, 13)}:
        errors.append("assigned denominator differs from frozen 24-opportunity cohort")

    summaries = {}
    for route, losses_by_oid in derived.items():
        if any(v is None for v in losses_by_oid.values()):
            continue
        vals = list(losses_by_oid.values())
        strata = {}
        for s in ("S1", "S2"):
            sv = [losses_by_oid[oid] for oid, m in meta.items() if m["stratum"] == s]
            strata[s] = {"n": len(sv), "mean": sum(sv)/len(sv), "es20": _es20(sv), "exceedance_ge_3": sum(v >= 3 for v in sv)}
        cluster_means = {}
        for cluster in sorted({m["cluster"] for m in meta.values()}):
            cv = [losses_by_oid[oid] for oid, m in meta.items() if m["cluster"] == cluster]
            cluster_means[cluster] = sum(cv)/len(cv)
        leave_one_cluster_out = []
        for cluster in cluster_means:
            remain = [losses_by_oid[oid] for oid, m in meta.items() if m["cluster"] != cluster]
            leave_one_cluster_out.append(sum(remain)/len(remain))
        summaries[route] = {
            "n": len(vals), "pooled_mean": sum(vals)/len(vals), "es20": _es20(vals),
            "exceedance_ge_3": {"count": sum(v >= 3 for v in vals), "denominator": len(vals), "rate": sum(v >= 3 for v in vals)/len(vals)},
            "strata": strata, "macro_mean": sum(x["mean"] for x in strata.values())/2,
            "macro_es20": sum(x["es20"] for x in strata.values())/2,
            "cluster_means": cluster_means,
            "delete_one_cluster_pooled_mean_range": [min(leave_one_cluster_out), max(leave_one_cluster_out)],
        }
    if summaries:
        for route, expected in EXPECTED_PRIMARY.items():
            actual = summaries.get(route, {})
            for field, value in expected.items():
                if actual.get(field) != value:
                    errors.append(f"frozen primary statistic mismatch {route}/{field}")
        if not (summaries.get("A", {}).get("pooled_mean") == summaries.get("B", {}).get("pooled_mean") and summaries.get("A", {}).get("es20", 0) > summaries.get("B", {}).get("es20", 0)):
            errors.append("preregistered mean/tail ranking contrast absent")
    controls = truth.get("controls", {})
    expected_controls = {"benign_extreme_spike": (1000, "OUT_OF_SCOPE_BENIGN", False), "missing_truth": ("UNKNOWN", None), "censored": ("UNRESOLVED_CENSORED", None), "hard_safety_violation": ("FAIL_HARD_SAFETY", None)}
    for name, fields in expected_controls.items():
        c = controls.get(name, {})
        if name == "benign_extreme_spike":
            if (c.get("value"), c.get("scope"), c.get("include_in_estimand")) != fields:
                errors.append("benign spike control changed or pooled")
        elif (c.get("status"), c.get("numeric_value")) != fields:
            errors.append(f"categorical control collapsed: {name}")
    mutations = _mutations(visible, truth, raw) if run_mutations else []
    if run_mutations and (len(mutations) != 6 or not all(m["rejected"] for m in mutations)):
        errors.append("one or more mutation controls escaped detection")
    return {"schema":"tail-regret-8597-independent-audit-v1", "disposition":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "errors":errors, "summaries":summaries, "opportunity_regret":derived, "assigned_opportunities":len(source_ops), "hard_safety_violations":len(hard_events), "controls":controls, "mutation_controls":mutations, "scope":"Finite synthetic method evidence only; no real route, task, causal, GUI, safety, or population-tail claim."}


def _mutations(visible, truth, raw):
    probes=[]
    r=copy.deepcopy(raw); r["rows"].pop(); probes.append(("drop_row",visible,truth,r))
    r=copy.deepcopy(raw); r["rows"].append(copy.deepcopy(r["rows"][0])); probes.append(("duplicate_row",visible,truth,r))
    v=copy.deepcopy(visible); v["assigned_opportunities"][0]["stratum"]="S2"; probes.append(("stratum_reassignment",v,truth,raw))
    t=copy.deepcopy(truth); t["target_state_by_tick"]["S1-O01"]["A"]["0"]="B"; probes.append(("loss_sign_flip",visible,t,raw))
    t=copy.deepcopy(truth); t["controls"]["censored"]["numeric_value"]=0; probes.append(("censor_as_zero",visible,t,raw))
    t=copy.deepcopy(truth); t["controls"]["hard_safety_violation"]["numeric_value"]=0; probes.append(("safety_to_scalar",visible,t,raw))
    outcomes=[]
    for name,v,t,r in probes:
        result=audit_payload(v,t,r,run_mutations=False)
        outcomes.append({"name":name,"rejected":bool(result["errors"])})
    return outcomes


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--dir",type=Path,default=Path(__file__).parent); root=parser.parse_args().dir
    v=json.loads((root/"visible.json").read_text()); t=json.loads((root/"truth.json").read_text()); r=json.loads((root/"candidate_raw.json").read_text())
    report=audit_payload(v,t,r)
    (root/"audit.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    rejected=sum(x["rejected"] for x in report["mutation_controls"])
    print(f"{report['disposition']} opportunities={report['assigned_opportunities']} errors={len(report['errors'])} mutations={rejected}/{len(report['mutation_controls'])}")
    return 0 if report["disposition"]=="PASS_METHOD_SCOPED" else 1

if __name__=="__main__": raise SystemExit(main())

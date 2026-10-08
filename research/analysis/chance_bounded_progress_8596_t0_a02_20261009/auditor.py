"""Independent path-enumerating auditor. Does not import candidate or runner."""
from __future__ import annotations
import argparse, copy, hashlib, itertools, json
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def ratio(text):
    a,b=text.split("/",1); return Fraction(int(a),int(b))


def text(q):
    return f"{q.numerator}/{q.denominator}"


def enumerate_histories(probabilities):
    """Return exact marker probability by enumerating every binary history."""
    total=Fraction(0)
    for history in itertools.product((False,True),repeat=len(probabilities)):
        mass=Fraction(1)
        for p,hit in zip(probabilities,history):
            mass *= p if hit else 1-p
        if any(history): total += mass
    return total


def independent_geometric(spec,horizons,tau):
    lo=ratio(spec["p_min"]); hi=ratio(spec["p_max"]); mid=(lo+hi)/2; curve=[]
    for horizon in horizons:
        rows=[]
        for choices in itertools.product((lo,hi),repeat=horizon):
            rows.append({"p_vector":[text(p) for p in choices],"reachability":text(enumerate_histories(choices)),"path_count":2**horizon})
        probabilities=[ratio(r["reachability"]) for r in rows]
        midpoint=enumerate_histories((mid,)*horizon)
        all_miss=(1-hi)**horizon
        curve.append({"horizon":horizon,"endpoint_rows":rows,"lower":text(min(probabilities)),"upper":text(max(probabilities)),"midpoint_probability":text(midpoint),"sure_by_horizon":all_miss==0,"all_miss_probability_at_max_endpoint":text(all_miss),"lower_meets_threshold":min(probabilities)>=tau,"midpoint_meets_threshold":midpoint>=tau})
    return {"kind":"geometric_interval","p_min":text(lo),"p_max":text(hi),"threshold":text(tau),"curve":curve,"universal_finite_sure_bound":False,"marker_visible_to_policy":False}


def independent_disturbance(spec,horizon,tau):
    lo=ratio(spec["p_min"]); hi=ratio(spec["p_max"]); q=ratio(spec["trigger"])
    # Trigger preempts the progress clock; without it, enumerate full N-step paths.
    g_lo=enumerate_histories((lo,)*horizon); g_hi=enumerate_histories((hi,)*horizon)
    outcomes=sorted(set(spec["trigger_outcomes"]))
    hard_safe="UNSAFE" not in outcomes
    low=(1-q)*g_lo; high=(1-q)*g_hi
    adv_low=Fraction(0) if "UNSAFE" in outcomes else low
    return {"kind":"geometric_with_trigger","trigger_probability":text(q),"trigger_outcomes":outcomes,"threshold":text(tau),"stochastic_bounds":{"lower":text(low),"upper":text(high)},"adversarial_worst_case_lower":text(adv_low),"hard_safety":"PASS" if hard_safe else "FAIL","universal_finite_sure_bound":False,"policy_disposition":"CONTINUE_SYNTHETIC" if hard_safe and low>=tau else "SAFE_YIELD","marker_visible_to_policy":False}


def independent_delay(spec,horizon):
    rows={}
    for arm in ("benign","rare_tail"):
        support=[(int(n),ratio(prob)) for n,prob in spec[arm]]
        mean=sum(Fraction(n)*prob for n,prob in support)
        within=sum(prob for n,prob in support if n<=horizon)
        tail=sum(prob for n,prob in support if n>horizon)
        rows[arm]={"support":[{"first_marker_opportunity":n,"probability":text(prob)} for n,prob in support],"mean_opportunities":text(mean),"probability_by_deadline":text(within),"probability_after_deadline":text(tail)}
    return {"kind":"delay_support_comparison","deadline":horizon,"arms":rows,"means_equal":rows["benign"]["mean_opportunities"]==rows["rare_tail"]["mean_opportunities"],"deadline_probabilities_differ":rows["benign"]["probability_by_deadline"]!=rows["rare_tail"]["probability_by_deadline"],"marker_visible_to_policy":False}


def expected_payload(fixtures):
    cases=fixtures["cases"]; hs=fixtures["horizons"]; tau=ratio(fixtures["illustrative_threshold"]); n=fixtures["primary_horizon"]
    values={
        "geometric_wide":independent_geometric(cases["geometric_wide"],hs,tau),
        "geometric_high":independent_geometric(cases["geometric_high"],hs,tau),
        "rare_disturbance_safe_yield":independent_disturbance(cases["rare_disturbance_safe_yield"],n,tau),
        "rare_disturbance_unsafe":independent_disturbance(cases["rare_disturbance_unsafe"],n,tau),
        "same_mean_delay":independent_delay(cases["same_mean_delay"],n),
        "unmodeled_delay":{"kind":"unknown","status":"NOT_IDENTIFIABLE","numeric_probability_reported":False,"marker_visible_to_policy":False}
    }
    wide=values["geometric_wide"]["curve"][n-1]; high=values["geometric_high"]["curve"][n-1]
    return {"allocation":fixtures["allocation"],"horizons":hs,"primary_horizon":n,"cases":values,"discriminator":{"horizon":n,"threshold":text(tau),"high_interval_lower_meets_threshold":high["lower_meets_threshold"],"high_interval_has_universal_finite_bound":values["geometric_high"]["universal_finite_sure_bound"],"wide_midpoint_meets_threshold":wide["midpoint_meets_threshold"],"wide_lower_meets_threshold":wide["lower_meets_threshold"],"same_mean_but_tail_differs":values["same_mean_delay"]["means_equal"] and values["same_mean_delay"]["deadline_probabilities_differ"],"unsafe_case_hard_safety_fails":values["rare_disturbance_unsafe"]["hard_safety"]=="FAIL","unknown_has_no_probability":not values["unmodeled_delay"]["numeric_probability_reported"]}}


def verify_sources(freeze):
    for name,digest in freeze["source_sha256"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest: return False
    return True


def audit(out):
    freeze=json.loads((ROOT/"FREEZE.json").read_text())
    if not verify_sources(freeze): raise ValueError("frozen source digest mismatch")
    fixtures=json.loads((ROOT/"fixtures.json").read_text())
    raw_path=out/"candidate.json"; raw=json.loads(raw_path.read_text()); expected=expected_payload(fixtures)
    if raw!=expected: raise ValueError("independent exhaustive enumeration mismatch")
    mutations={}
    probes={
        "forged_interval_bound":lambda x:x["cases"]["geometric_wide"]["curve"][3].__setitem__("lower","1/1"),
        "midpoint_substituted_for_lower":lambda x:x["cases"]["geometric_wide"]["curve"][3].__setitem__("lower",x["cases"]["geometric_wide"]["curve"][3]["midpoint_probability"]),
        "false_finite_sure_bound":lambda x:x["cases"]["geometric_high"].__setitem__("universal_finite_sure_bound",True),
        "dropped_rare_tail_atom":lambda x:x["cases"]["same_mean_delay"]["arms"]["rare_tail"]["support"].pop(),
        "unsafe_transition_relabelled_safe":lambda x:x["cases"]["rare_disturbance_unsafe"].__setitem__("hard_safety","PASS"),
        "unknown_probability_imputed":lambda x:x["cases"]["unmodeled_delay"].__setitem__("numeric_probability_reported",True),
        "marker_oracle_leaked":lambda x:x["cases"]["geometric_high"].__setitem__("marker_visible_to_policy",True)
    }
    for name,mutate in probes.items():
        changed=copy.deepcopy(raw); mutate(changed); mutations[name]=changed!=expected
    if not all(mutations.values()): raise ValueError("mutation control missed")
    d=expected["discriminator"]
    supported=(d["high_interval_lower_meets_threshold"] and not d["high_interval_has_universal_finite_bound"] and d["wide_midpoint_meets_threshold"] and not d["wide_lower_meets_threshold"] and d["same_mean_but_tail_differs"] and d["unsafe_case_hard_safety_fails"] and d["unknown_has_no_probability"])
    result={"allocation":freeze["allocation"],"disposition":"H_SUPPORTED_SCOPED" if supported else "H_FAIL_SCOPED","method_gate":"PASS_METHOD_SCOPED","candidate_sha256":hashlib.sha256(raw_path.read_bytes()).hexdigest(),"exact_independent_match":True,"geometric_endpoint_vectors_checked":sum(len(c["curve"][n-1]["endpoint_rows"]) for key,c in expected["cases"].items() if c["kind"]=="geometric_interval" for n in [expected["primary_horizon"]]),"binary_progress_histories_per_endpoint_at_primary_horizon":2**expected["primary_horizon"],"primary_horizon":expected["primary_horizon"],"threshold_fixture_only":expected["discriminator"]["threshold"],"wide_interval":{"lower":expected["cases"]["geometric_wide"]["curve"][expected["primary_horizon"]-1]["lower"],"midpoint":expected["cases"]["geometric_wide"]["curve"][expected["primary_horizon"]-1]["midpoint_probability"],"upper":expected["cases"]["geometric_wide"]["curve"][expected["primary_horizon"]-1]["upper"]},"high_interval":{"lower":expected["cases"]["geometric_high"]["curve"][expected["primary_horizon"]-1]["lower"],"sure_finite_bound":False},"same_mean_delay":{"benign_mean":expected["cases"]["same_mean_delay"]["arms"]["benign"]["mean_opportunities"],"rare_tail_mean":expected["cases"]["same_mean_delay"]["arms"]["rare_tail"]["mean_opportunities"],"benign_by_deadline":expected["cases"]["same_mean_delay"]["arms"]["benign"]["probability_by_deadline"],"rare_tail_by_deadline":expected["cases"]["same_mean_delay"]["arms"]["rare_tail"]["probability_by_deadline"]},"unsafe_case_hard_safety":expected["cases"]["rare_disturbance_unsafe"]["hard_safety"],"unknown_status":expected["cases"]["unmodeled_delay"]["status"],"mutations":mutations,"errors":0,"scope":"authored finite exact-rational CPU model only"}
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default=str(ROOT/"results/first-outcome")); ap.add_argument("--result",default=str(ROOT/"results/first-outcome/audit.json")); args=ap.parse_args()
    summary=audit(Path(args.output)); target=Path(args.result); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n"); print(json.dumps(summary,sort_keys=True))

if __name__=="__main__": main()

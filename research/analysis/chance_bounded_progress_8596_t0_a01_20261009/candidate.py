"""Exact-rational dynamic-programming candidate for Issue #8596 T0 A01."""
from __future__ import annotations
from fractions import Fraction
from itertools import product


def f(text):
    return Fraction(text)


def qs(value):
    return f"{value.numerator}/{value.denominator}"


def dynamic_hit(probabilities):
    alive=Fraction(1); hit=Fraction(0)
    for p in probabilities:
        hit += alive*p
        alive *= 1-p
    return hit


def geometric_case(spec,horizons,tau):
    low=f(spec["p_min"]); high=f(spec["p_max"]); mid=(low+high)/2
    curve=[]
    for n in horizons:
        endpoint_rows=[]
        for bits in product((0,1),repeat=n):
            probs=tuple(high if bit else low for bit in bits)
            endpoint_rows.append({"p_vector":[qs(p) for p in probs],"reachability":qs(dynamic_hit(probs)),"path_count":2**n})
        values=[f(row["reachability"]) for row in endpoint_rows]
        midpoint=dynamic_hit((mid,)*n)
        # Every p is strictly below one, so the all-miss history has positive mass.
        all_miss_mass=(1-high)**n
        curve.append({"horizon":n,"endpoint_rows":endpoint_rows,"lower":qs(min(values)),"upper":qs(max(values)),"midpoint_probability":qs(midpoint),"sure_by_horizon":all_miss_mass==0,"all_miss_probability_at_max_endpoint":qs(all_miss_mass),"lower_meets_threshold":min(values)>=tau,"midpoint_meets_threshold":midpoint>=tau})
    return {"kind":"geometric_interval","p_min":qs(low),"p_max":qs(high),"threshold":qs(tau),"curve":curve,"universal_finite_sure_bound":False,"marker_visible_to_policy":False}


def disturbance_case(spec,horizon,tau,unsafe):
    lo=f(spec["p_min"]); hi=f(spec["p_max"]); q=f(spec["trigger"])
    geometric_low=dynamic_hit((lo,)*horizon); geometric_high=dynamic_hit((hi,)*horizon)
    outcomes=set(spec["trigger_outcomes"])
    hard_safe="UNSAFE" not in outcomes
    # The trigger occurs before the counted progress opportunities. If absent,
    # the ordinary geometric process receives the full frozen deadline.
    l=(1-q)*geometric_low; u=(1-q)*geometric_high
    worst_adversarial_lower=Fraction(0) if "UNSAFE" in outcomes else l
    return {"kind":"geometric_with_trigger","trigger_probability":qs(q),"trigger_outcomes":sorted(outcomes),"threshold":qs(tau),"stochastic_bounds":{"lower":qs(l),"upper":qs(u)},"adversarial_worst_case_lower":qs(worst_adversarial_lower),"hard_safety":"PASS" if hard_safe else "FAIL","universal_finite_sure_bound":False,"policy_disposition":"CONTINUE_SYNTHETIC" if hard_safe and l>=tau else "SAFE_YIELD","marker_visible_to_policy":False}


def delay_case(spec,horizon):
    rows={}
    for arm in ("benign","rare_tail"):
        support=[(int(n),f(prob)) for n,prob in spec[arm]]
        mean=sum(Fraction(n)*prob for n,prob in support)
        within=sum(prob for n,prob in support if n<=horizon)
        tail=sum(prob for n,prob in support if n>horizon)
        rows[arm]={"support":[{"first_marker_opportunity":n,"probability":qs(prob)} for n,prob in support],"mean_opportunities":qs(mean),"probability_by_deadline":qs(within),"probability_after_deadline":qs(tail)}
    return {"kind":"delay_support_comparison","deadline":horizon,"arms":rows,"means_equal":rows["benign"]["mean_opportunities"]==rows["rare_tail"]["mean_opportunities"],"deadline_probabilities_differ":rows["benign"]["probability_by_deadline"]!=rows["rare_tail"]["probability_by_deadline"],"marker_visible_to_policy":False}


def evaluate(fixtures):
    cases=fixtures["cases"]; horizons=fixtures["horizons"]; tau=f(fixtures["illustrative_threshold"]); n=fixtures["primary_horizon"]
    out={}
    out["geometric_wide"]=geometric_case(cases["geometric_wide"],horizons,tau)
    out["geometric_high"]=geometric_case(cases["geometric_high"],horizons,tau)
    out["rare_disturbance_safe_yield"]=disturbance_case(cases["rare_disturbance_safe_yield"],n,tau,False)
    out["rare_disturbance_unsafe"]=disturbance_case(cases["rare_disturbance_unsafe"],n,tau,True)
    out["same_mean_delay"]=delay_case(cases["same_mean_delay"],n)
    out["unmodeled_delay"]={"kind":"unknown","status":"NOT_IDENTIFIABLE","numeric_probability_reported":False,"marker_visible_to_policy":False}
    wide=out["geometric_wide"]["curve"][n-1]; high=out["geometric_high"]["curve"][n-1]
    discriminator={"horizon":n,"threshold":qs(tau),"high_interval_lower_meets_threshold":high["lower_meets_threshold"],"high_interval_has_universal_finite_bound":out["geometric_high"]["universal_finite_sure_bound"],"wide_midpoint_meets_threshold":wide["midpoint_meets_threshold"],"wide_lower_meets_threshold":wide["lower_meets_threshold"],"same_mean_but_tail_differs":out["same_mean_delay"]["means_equal"] and out["same_mean_delay"]["deadline_probabilities_differ"],"unsafe_case_hard_safety_fails":out["rare_disturbance_unsafe"]["hard_safety"]=="FAIL","unknown_has_no_probability":not out["unmodeled_delay"]["numeric_probability_reported"]}
    return {"allocation":fixtures["allocation"],"horizons":horizons,"primary_horizon":n,"cases":out,"discriminator":discriminator}

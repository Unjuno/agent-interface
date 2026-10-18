#!/usr/bin/env python3
"""Independent schedule/effect-oracle reconstruction; no candidate imports."""
import functools, json, random, sys


def reconstruct(cases, scoring, raw):
    errors=[]; gate=cases["eligibility"]; pair_order=cases["pair_order"]
    if raw.get("schema") != "issue8084-practice-t0-v1" or len(raw.get("rows",[])) != len(cases["cases"]): errors.append("shape")
    rows={row.get("case_id"):row for row in raw.get("rows",[])}
    if len(rows) != len(raw.get("rows",[])): errors.append("duplicate-case")
    for index, case in enumerate(cases["cases"]):
        got=rows.get(case["id"])
        if got is None: errors.append("missing-case:"+case["id"]); continue
        values=case["confusion"]; lo,hi=min(values),max(values); peak=hi
        eligible=(hi-lo >= gate["minimum_span"] and peak >= gate["minimum_peak"])
        target=pair_order[max(range(len(values)),key=lambda j:(values[j],-j))]
        variant_set=set(case["variants"]); quota=cases["attempts_per_variant"]; cap=cases["max_identical_run"]
        # Rebuild the deterministic random comparator independently.
        expected_random=[v for v in case["variants"] for _ in range(quota)]
        rng=random.Random(index+101)
        for _ in range(10000):
            rng.shuffle(expected_random)
            if max_run(expected_random) <= cap: break
        else: errors.append("random-generator:"+case["id"])
        expected_adaptive=optimal_sequence(case["variants"],quota,cap,target) if eligible else expected_random
        for arm, seq in (("random",got.get("random")),("adaptive",got.get("adaptive"))):
            if not isinstance(seq,list) or len(seq)!=len(variant_set)*quota:
                errors.append(f"length:{case['id']}:{arm}"); continue
            if set(seq)-variant_set or any(seq.count(v)!=quota for v in variant_set): errors.append(f"exposure:{case['id']}:{arm}")
            if max_run(seq)>cap: errors.append(f"run-cap:{case['id']}:{arm}")
            if any(v in set(scoring.get("heldout",[])) for v in seq): errors.append(f"heldout-leak:{case['id']}:{arm}")
        if (got.get("eligible"),got.get("confusion_span"),got.get("peak_confusion"),got.get("target_pair")) != (eligible,hi-lo,peak,target): errors.append("gate:"+case["id"])
        if got.get("random") != expected_random: errors.append("random-replay:"+case["id"])
        if got.get("adaptive") != expected_adaptive: errors.append("adaptive-replay:"+case["id"])
        expected_mode="ADAPTIVE" if eligible else "NEUTRAL_FALLBACK"
        if got.get("adaptive_mode") != expected_mode: errors.append("mode:"+case["id"])
    expected_scores=[{"id":t["id"],"score":score_independent(t,scoring)} for t in scoring["traces"]]
    if raw.get("scoring_controls") != expected_scores: errors.append("scoring-controls")
    decision="METHOD_PASS_SCOPED" if not errors else "HOLD_METHOD_GATE"
    return {"decision":decision,"errors":errors,"matrix_cases":len(cases["cases"]),
            "schedule_rows":2*len(cases["cases"]),"scoring_controls":len(scoring["traces"]),
            "human_effect":"NOT_TESTED","scope":"synthetic schedule/method readiness only"}


def max_run(seq):
    best=run=0; prev=None
    for x in seq:
        run=run+1 if x==prev else 1; best=max(best,run); prev=x
    return best


def optimal_sequence(variants, quota, cap, pair):
    @functools.lru_cache(None)
    def visit(counts,last,run):
        if sum(counts)==0:return (0,())
        best=None
        for i,v in enumerate(variants):
            if not counts[i] or (v==last and run>=cap):continue
            rest=list(counts);rest[i]-=1
            nr=run+1 if v==last else 1
            gain=int((last,v)==tuple(pair) or (v,last)==tuple(pair))
            points,tail=visit(tuple(rest),v,nr);candidate=(gain+points,(v,)+tail)
            if best is None or candidate[0]>best[0] or (candidate[0]==best[0] and candidate[1]<best[1]):best=candidate
        return best if best is not None else (-10**6,())
    return list(visit(tuple(quota for _ in variants),"",0)[1])


def score_independent(trace,oracle):
    allowed=set(oracle["family"])
    if trace["intent"] not in allowed:return "UNKNOWN_OUTSIDE_FAMILY"
    if trace["observed_target"]!=trace["intent"]:return "REJECT_WRONG_TARGET"
    if trace["observed_effect"]!=oracle["expected_effect"][trace["intent"]]:return "REJECT_FALSE_SUCCESS"
    return "VALID_EXACT_EFFECT" if trace["success_claim"] is True else "NO_SUCCESS_CLAIM"


if __name__=="__main__":
    with open("cases.json",encoding="utf-8") as f:cases=json.load(f)
    with open("scoring_cases.json",encoding="utf-8") as f:scoring=json.load(f)
    with open(sys.argv[1],encoding="utf-8") as f:raw=json.load(f)
    json.dump(reconstruct(cases,scoring,raw),sys.stdout,sort_keys=True,indent=2);print()

#!/usr/bin/env python3
"""Independent raw-only schedule and effect-truth reconstruction."""
import functools,json,random,sys


def max_streak(items):
    best=run=0;last=object()
    for item in items:
        run=run+1 if item==last else 1;best=max(best,run);last=item
    return best


def neutral_expected(variants,count,limit,seed):
    seq=[]
    for v in variants:seq.extend([v]*count)
    gen=random.Random(seed)
    for _ in range(10000):
        gen.shuffle(seq)
        if max_streak(seq)<=limit:return seq
    return []


def enumerate_best(variants,count,limit,edge):
    edge=frozenset(edge)
    @functools.lru_cache(None)
    def visit(rem,prior,streak):
        if not any(rem):return (0,())
        winner=None
        for k,node in enumerate(variants):
            if rem[k]<1 or (node==prior and streak==limit):continue
            tail=list(rem);tail[k]-=1;next_streak=streak+1 if node==prior else 1
            value,order=visit(tuple(tail),node,next_streak)
            points=value+int(bool(prior) and node!=prior and frozenset((prior,node))==edge)
            option=(points,(node,)+order)
            if winner is None or points>winner[0] or (points==winner[0] and option[1]<winner[1]):winner=option
        return winner if winner is not None else (-999999,())
    return list(visit(tuple(count for _ in variants),"",0)[1])


def judge(trace,truth):
    if trace["intent"] not in truth["family"]:return "UNKNOWN_OUTSIDE_FAMILY"
    if trace["observed_target"]!=trace["intent"]:return "REJECT_WRONG_TARGET"
    if trace["observed_effect"]!=truth["expected_effect"][trace["intent"]]:return "REJECT_FALSE_SUCCESS"
    return "VALID_EXACT_EFFECT" if trace["success_claim"] is True else "NO_SUCCESS_CLAIM"


def audit(cases,truth,raw):
    errors=[];gate=cases["eligibility"];indexed={x.get("case_id"):x for x in raw.get("rows",[])}
    if raw.get("schema")!="issue8084-practice-a02-v1" or len(indexed)!=len(cases["cases"]):errors.append("shape")
    for n,c in enumerate(cases["cases"]):
        row=indexed.get(c["id"])
        if row is None:errors.append("missing:"+c["id"]);continue
        scores=c["confusion"];spread=max(scores)-min(scores);peak=max(scores)
        enabled=spread>=gate["minimum_span"] and peak>=gate["minimum_peak"]
        pair=cases["pair_order"][max(range(len(scores)),key=lambda k:(scores[k],-k))]
        neutral_seq=neutral_expected(c["variants"],cases["attempts_per_variant"],cases["max_identical_run"],n+101)
        optimal=enumerate_best(c["variants"],cases["attempts_per_variant"],cases["max_identical_run"],pair)
        for arm in ("random","adaptive"):
            order=row.get(arm)
            if not isinstance(order,list) or len(order)!=len(c["variants"])*cases["attempts_per_variant"]:
                errors.append(f"length:{c['id']}:{arm}");continue
            if set(order)-set(c["variants"]):errors.append(f"variant-leak:{c['id']}:{arm}")
            if any(order.count(v)!=cases["attempts_per_variant"] for v in c["variants"]):errors.append(f"quota:{c['id']}:{arm}")
            if max_streak(order)>cases["max_identical_run"]:errors.append(f"streak:{c['id']}:{arm}")
            if set(order)&set(truth["heldout"]):errors.append(f"heldout:{c['id']}:{arm}")
        expected_order=optimal if enabled else neutral_seq
        expected_mode="ADAPTIVE" if enabled else "NEUTRAL_FALLBACK"
        if row.get("eligible")!=enabled or row.get("target_pair")!=pair or row.get("adaptive")!=expected_order or row.get("random")!=neutral_seq or row.get("mode")!=expected_mode:
            errors.append("reconstruction:"+c["id"])
    scores=[{"id":x["id"],"score":judge(x,truth)} for x in truth["traces"]]
    disposition="METHOD_PASS_SCOPED" if not errors else "HOLD_METHOD_GATE"
    return {"decision":disposition,"errors":errors,"matrix_cases":len(cases["cases"]),
            "schedule_rows":2*len(cases["cases"]),"scoring_controls":scores,
            "human_effect":"NOT_TESTED","scope":"synthetic schedule and scorer method readiness only"}


if __name__=="__main__":
    with open("cases.json",encoding="utf-8") as f:cases=json.load(f)
    with open("scoring_cases.json",encoding="utf-8") as f:truth=json.load(f)
    with open(sys.argv[1],encoding="utf-8") as f:raw=json.load(f)
    json.dump(audit(cases,truth,raw),sys.stdout,sort_keys=True,indent=2);print()

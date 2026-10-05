#!/usr/bin/env python3
"""Candidate can read only cases.json: no scorer truth or held-out identifiers."""
import functools,json,random,sys


def streak(seq):
    best=run=0;prev=None
    for x in seq:
        run=run+1 if x==prev else 1;best=max(best,run);prev=x
    return best


def neutral(variants,n,cap,seed):
    items=[v for v in variants for _ in range(n)];rng=random.Random(seed)
    for _ in range(10000):
        rng.shuffle(items)
        if streak(items)<=cap:return list(items)
    raise RuntimeError("neutral order unavailable")


def pair_optimum(variants,n,cap,pair):
    pair=tuple(pair)
    @functools.lru_cache(None)
    def go(left,last,run):
        if not sum(left):return (0,())
        best=None
        for i,v in enumerate(variants):
            if left[i]==0 or (v==last and run>=cap):continue
            nxt=list(left);nxt[i]-=1;nr=run+1 if v==last else 1
            gain=int((last,v)==pair or (v,last)==pair)
            score,tail=go(tuple(nxt),v,nr);option=(gain+score,(v,)+tail)
            if best is None or option[0]>best[0] or (option[0]==best[0] and option[1]<best[1]):best=option
        return best if best is not None else (-10**6,())
    out=list(go(tuple(n for _ in variants),"",0)[1])
    if len(out)!=len(variants)*n:raise RuntimeError("pair schedule unavailable")
    return out


def execute(source):
    gate=source["eligibility"];out=[]
    for i,c in enumerate(source["cases"]):
        vals=c["confusion"];eligible=max(vals)-min(vals)>=gate["minimum_span"] and max(vals)>=gate["minimum_peak"]
        j=max(range(len(vals)),key=lambda k:(vals[k],-k));pair=source["pair_order"][j]
        base=neutral(c["variants"],source["attempts_per_variant"],source["max_identical_run"],i+101)
        chosen=pair_optimum(c["variants"],source["attempts_per_variant"],source["max_identical_run"],pair) if eligible else base
        out.append({"case_id":c["id"],"eligible":eligible,"target_pair":pair,
                    "random":base,"adaptive":chosen,"mode":"ADAPTIVE" if eligible else "NEUTRAL_FALLBACK"})
    return {"schema":"issue8084-practice-a02-v1","rows":out}


if __name__=="__main__":
    with open("cases.json",encoding="utf-8") as f: data=json.load(f)
    json.dump(execute(data),sys.stdout,sort_keys=True,separators=(",",":"));print()

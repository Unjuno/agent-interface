#!/usr/bin/env python3
"""Independent raw-only verifier for Issue #5184 (stdlib, no candidate imports)."""
import hashlib, json, math, random, sys
import os
from pathlib import Path

SEEDS=(484421,484422); MODES=5; MAP=(0,0,1,2,2)
P=((0,0,0,0,0,0),(1,1,1,1,1,1),(0,1,0,1,0,1),(1,0,1,0,1,0),(0,0,1,1,0,1))
BLOCKS=("COMPLETE","SINGLE_MISSING","MULTI_MISSING","COMPOSITION_HOLDOUT","NUISANCE_SHIFT")

def independent_sample(rng, mode, block):
    v=list(P[mode])
    if block=="COMPOSITION_HOLDOUT": v[0]^=1; v[5]^=1
    elif block=="NUISANCE_SHIFT": v[3]^=1
    observed=[True]*6
    if block=="SINGLE_MISSING": observed[1]=False
    elif block=="MULTI_MISSING": observed[1]=observed[4]=False
    for j in range(6):
        if rng.random()<0.08: v[j]^=1
    if block!="COMPLETE":
        for j in range(6):
            if rng.random()<0.20: observed[j]=False
    return [v[j] if observed[j] else -1 for j in range(6)]

def train():
    rng=random.Random(SEEDS[0]); xs=[]; labels=[]
    for i in range(2000):
        m=i%5; xs.append(independent_sample(rng,m,"TRAIN")); labels.append(m)
    def learn(target, n):
        prior=[0]*n; yes=[[0]*6 for _ in range(n)]; seen=[[0]*6 for _ in range(n)]
        for x,y in zip(xs,target):
            prior[y]+=1
            for j,v in enumerate(x):
                if v!=-1: seen[y][j]+=1; yes[y][j]+=v
        return prior,yes,seen
    return learn([MAP[m] for m in labels],3),learn(labels,5)

def probs(x, model):
    prior,yes,seen=model; scores=[]
    for c in range(len(prior)):
        z=math.log((prior[c]+1)/(sum(prior)+len(prior)))
        for j,v in enumerate(x):
            if v==-1: continue
            q=(yes[c][j]+1)/(seen[c][j]+2); z+=math.log(q if v else 1-q)
        scores.append(z)
    peak=max(scores); es=[math.exp(q-peak) for q in scores]; total=sum(es)
    return [v/total for v in es]

def choice(x, models):
    dmod,tmod=models; a=probs(x,dmod); b=probs(x,tmod)
    def pick(q):
        ix=sorted(range(len(q)),key=lambda k:(-q[k],k)); margin=q[ix[0]]-(q[ix[1]] if len(ix)>1 else 0)
        return (ix[0] if q[ix[0]]>=0.65 and margin>=0 else None),q[ix[0]],margin
    d,dc,dm=pick(a); agg=[sum(b[k] for k in range(5) if MAP[k]==j) for j in range(3)]
    t,tc,tm=pick(agg)
    return d,t,dc,dm,tc,tm

def fail(ok, message):
    if not ok: raise ValueError(message)

def validate(doc):
    fail(doc["allocation"]=="typed-mode-4844-successor-20260928-02","allocation")
    fail((doc["seed_train"],doc["seed_test"])==SEEDS,"seeds")
    fail(doc["n_train"]==2000 and doc["n_test"]==4800 and len(doc["rows"])==4800,"row cardinality")
    fail(tuple(doc["blocks"].keys())==BLOCKS,"block order")
    fail(doc["config"]=={"alpha":1.0,"flip_p":0.08,"drop_p":0.2,"threshold":0.65,"margin":0.0,
         "dispositions":list(MAP),"prototypes":[list(x) for x in P]},"frozen config")
    models=train(); rng=random.Random(SEEDS[1]); cursor=0
    sums={b:{"n":0,"direct_wrong":0,"typed_wrong":0,"direct_coverage":0,"typed_coverage":0,"direct_unsafe":0,"typed_unsafe":0} for b in BLOCKS}
    for block in BLOCKS:
        for i in range(960):
            row=doc["rows"][cursor]; mode=i%5; x=independent_sample(rng,mode,block); truth=MAP[mode]
            fail(row["block"]==block and row["mode"]==mode and row["truth"]==truth and row["x"]==x,"raw row/source reconstruction")
            d,t,dc,dm,tc,tm=choice(x,models)
            for k,v in (("direct",d),("typed",t)): fail(row[k]==v,"prediction reconstruction")
            for k,v in (("direct_confidence",dc),("direct_margin",dm),("typed_confidence",tc),("typed_margin",tm)):
                fail(abs(row[k]-v)<1e-12,"posterior reconstruction")
            fail(row["direct_wrong"]==(d is not None and d!=truth) and row["typed_wrong"]==(t is not None and t!=truth),"error flags")
            fail(row["direct_coverage"]==(d is not None) and row["typed_coverage"]==(t is not None),"coverage flags")
            s=sums[block]; s["n"]+=1; s["direct_wrong"]+=int(d is not None and d!=truth); s["typed_wrong"]+=int(t is not None and t!=truth)
            s["direct_coverage"]+=int(d is not None); s["typed_coverage"]+=int(t is not None); cursor+=1
    for b in BLOCKS:
        s=sums[b]; n=s["n"]
        expected={"n":n,"direct_wrong":s["direct_wrong"],"typed_wrong":s["typed_wrong"],
          "direct_coverage":s["direct_coverage"]/n,"typed_coverage":s["typed_coverage"]/n,"direct_unsafe":0,"typed_unsafe":0}
        for k,v in expected.items():
            actual=doc["blocks"][b][k]
            fail(abs(actual-v)<1e-12 if isinstance(v,float) else actual==v,"summary "+b+"/"+k)
    pctrl=[]
    for mode,x in enumerate(P):
        d,t,*_=choice(list(x),models); pctrl.append({"kind":"prototype","mode":mode,"expected":MAP[mode],"direct":d,"typed":t})
    fail(doc["prototype_controls"]==pctrl,"prototype controls")
    fctrl=[]
    for kind,x in (("unknown",[-1]*6),("contradictory",[0,0,0,1,0,1])):
        d,t,*_=choice(x,models); fctrl.append({"kind":kind,"direct":d,"typed":t})
    fail(doc["fail_closed_controls"]==fctrl,"fail-closed controls")

def corruptions(doc):
    import copy
    cases=[]
    def add(f):
        x=copy.deepcopy(doc); f(x); cases.append(x)
    add(lambda x:x.update(allocation="wrong")); add(lambda x:x.update(seed_train=0)); add(lambda x:x.update(n_train=1999))
    add(lambda x:x["rows"].pop()); add(lambda x:x["rows"][0].update(block="wrong")); add(lambda x:x["rows"][0].update(mode=4))
    add(lambda x:x["rows"][0].update(truth=2)); add(lambda x:x["rows"][0]["x"].__setitem__(0,1))
    add(lambda x:x["rows"][0].update(direct=2)); add(lambda x:x["rows"][0].update(typed=1))
    add(lambda x:x["rows"][0].update(direct_wrong=not x["rows"][0]["direct_wrong"]))
    add(lambda x:x["rows"][0].update(typed_coverage=not x["rows"][0]["typed_coverage"]))
    add(lambda x:x["blocks"][BLOCKS[0]].update(direct_wrong=x["blocks"][BLOCKS[0]]["direct_wrong"]+1))
    add(lambda x:x["blocks"][BLOCKS[1]].update(typed_coverage=0.123))
    add(lambda x:x["prototype_controls"][0].update(expected=2))
    add(lambda x:x["fail_closed_controls"][0].update(direct=1))
    rejected=0
    for c in cases:
        try: validate(c)
        except (AssertionError,ValueError,KeyError,TypeError,IndexError): rejected+=1
    fail(rejected==16,"corruption matrix")
    return rejected

def main():
    path=Path(sys.argv[1]); raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    fail(digest==sys.argv[2],"result digest")
    doc=json.loads(raw); validate(doc); n=corruptions(doc)
    receipt={"pass":True,"errors":[],"rows":4800,"corruption_controls_rejected":n,"result_sha256":digest}
    text=json.dumps(receipt,sort_keys=True,separators=(",",":"))
    out=Path(os.environ.get("AUDIT_DIR","/audit")); out.mkdir(parents=True,exist_ok=True); (out/"audit.json").write_text(text+"\n",encoding="utf-8")
    print(text)

if __name__=="__main__": main()

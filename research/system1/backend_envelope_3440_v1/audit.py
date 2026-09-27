"""Independent standard-library audit. Does not import experiment.py or torch."""
import json, math, random, sys
from pathlib import Path

LABELS = ("LEFT", "RIGHT", "HOLD", "REACQUIRE", "YIELD", "NO_ACTION")

def oracle(x):
    dx,dy,vx,vy,conf,age,track,settle,phase,visible,scope,done=x
    if done>.5:return 5
    if scope<.5:return 4
    if visible<.5 or conf<.28 or age>.72:return 3
    lx=dx+.42*vx+(.22*vx if settle>.5 else 0)
    ly=dy+.42*vy+(.22*vy if settle>.5 else 0)
    th=.13+.045*phase
    if abs(lx)<=th and abs(ly)<=th:return 2
    if abs(lx)>abs(ly):return 0 if lx<0 else 1
    return 2 if abs(ly)<=th*1.65 else (0 if ly<0 else 1)

def expected(seed,n,shifted=False):
    rng=random.Random(seed); rows=[]
    for _ in range(n):
        s=1.65 if shifted else 1.; dx=rng.uniform(-s,s);dy=rng.uniform(-s,s)
        vx=rng.uniform(-.95,.95)+(rng.choice((-.7,.7)) if shifted and rng.random()<.22 else 0)
        vy=rng.uniform(-.95,.95)+(rng.choice((-.7,.7)) if shifted and rng.random()<.22 else 0)
        intent=rng.randrange(2);phase=rng.random();conf=rng.uniform(.55,1);age=rng.uniform(0,.35);noise=.13 if shifted else .045
        dx+=rng.gauss(0,noise);dy+=rng.gauss(0,noise)
        rows.append([dx,dy,vx,vy,conf,age,float(intent==0),float(intent==1),phase,1.,1.,0.])
    return rows

def rule(x):
    if x[11]>.5:return 5
    if x[10]<.5:return 4
    if x[9]<.5 or x[4]<.4 or x[5]>.5:return 3
    px=x[0]+.12*x[2];py=x[1]+.12*x[3]
    if abs(px)<.18 and abs(py)<.18:return 2
    if abs(px)>abs(py):return 0 if px<0 else 1
    return 0 if py<0 else 1

def tree_predict(t,x):
    while "feature" in t:t=t["left"] if x[t["feature"]]<=t["cut"] else t["right"]
    return t["pred"]

def mlp_predict(state,x):
    a=x
    for layer in (0,2,4):
        w,b=state[f"{layer}.weight"],state[f"{layer}.bias"]
        a=[sum(w[j][i]*a[i] for i in range(len(a)))+b[j] for j in range(len(w))]
        if layer!=4:a=[math.tanh(v) for v in a]
    return max(range(6),key=lambda i:(a[i],-i))

def main(path):
    d=json.loads(Path(path).read_text(encoding="utf-8")); seed=d["seed"]
    assert d["n_train"]==512 and set(d["groups"])=={"iid","shift","controls"}
    specs={"iid":(seed+100000,1024,False),"shift":(seed+200000,1024,True)}
    errors=[]
    for group,(ds,n,shift) in specs.items():
        g=d["groups"][group]; rows=expected(ds,n,shift); labels=[oracle(x) for x in rows]
        assert rows==g["rows"],f"{group} data regeneration mismatch"
        assert labels==g["labels"],f"{group} oracle label mismatch"
        for backend in ("rule","tree","mlp"):
            pred=g["predictions"][backend]
            fn={"rule":rule,"tree":lambda x:tree_predict(d["models"]["tree"],x),"mlp":lambda x:mlp_predict(d["models"]["mlp"],x)}[backend]
            recalc=[fn(x) for x in rows]; errors += [(group,backend,i) for i,(a,b) in enumerate(zip(pred,recalc)) if a!=b]
            safe=[i for i,x in enumerate(rows) if x[9]>.5 and x[10]>.5 and x[11]<.5 and x[4]>=.28 and x[5]<=.72]
            m=g["metrics"][backend]
            cov=sum(pred[i]==labels[i] for i in safe)/len(safe)
            prec=sum(pred[i]==labels[i] for i in safe)/max(1,sum(pred[i] in (0,1,2) for i in safe))
            assert abs(m["coverage"]-cov)<1e-12 and abs(m["actionable_precision"]-prec)<1e-12
    cg=d["groups"]["controls"]
    assert len(cg["rows"])==4
    for i,x in enumerate(cg["rows"]):assert oracle(x)==cg["labels"][i]
    summary={b:d["groups"]["shift"]["metrics"][b] for b in ("rule","tree","mlp")}
    print(json.dumps({"audit":"PASS" if not errors else "FAIL","prediction_mismatches":len(errors),"shift_metrics":summary,"latency_records":d["latency"]},sort_keys=True))
    if errors:sys.exit(2)

if __name__=="__main__":main(sys.argv[1])

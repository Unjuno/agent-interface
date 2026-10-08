import json, sys
from fractions import Fraction as R
from pathlib import Path

POLICY=("A_HORIZON_NEAREST","B_SLOT_NEAREST","C_ERROR_CARRY","D_RELEASE")

def in_hull(v, name):
    x,y=v
    return abs(x)+abs(y)<=1 if name=="4way" else max(abs(x),abs(y))<=1

def replay(case, alphabet, arm):
    v=tuple(R(q) for q in case["intent"]); n=case["horizon"]
    acts=[tuple(R(q) for q in a) for a in alphabet]
    if case.get("control")=="unknown_calibration":
        return {"status":"REFUSE_UNKNOWN_CALIBRATION","moves":[],"positions":[],"release":True,"switches":0}
    if not in_hull(v,case["action_set"]):
        return {"status":"REFUSE_OUTSIDE_HULL","moves":[],"positions":[],"release":True,"switches":0}
    if arm==POLICY[3]: seq=[(R(0),R(0)) for _ in range(n)]
    elif arm in POLICY[:2]:
        idx=min(range(len(acts)),key=lambda j:((acts[j][0]-v[0])**2+(acts[j][1]-v[1])**2,j))
        seq=[acts[idx]]*n
    else:
        seq=[]; px=R(0); py=R(0)
        for slot in range(1,n+1):
            rank=[]
            for j,(ax,ay) in enumerate(acts):
                ex=slot*v[0]-px-ax; ey=slot*v[1]-py-ay
                rank.append((ex*ex+ey*ey,j,ax,ay))
            _,_,ax,ay=min(rank); seq.append((ax,ay)); px+=ax; py+=ay
    px=R(0); py=R(0); trail=[]; errs=[]; bad=0
    xmin,xmax,ymin,ymax=(R(q) for q in case["box"])
    for slot,(ax,ay) in enumerate(seq,1):
        px+=ax; py+=ay; trail.append([str(px),str(py)])
        dx=px-slot*v[0]; dy=py-slot*v[1]; errs.append(str(dx*dx+dy*dy))
        bad+=int(not(xmin<=px<=xmax and ymin<=py<=ymax))
    turns=sum(seq[k]!=seq[k-1] for k in range(1,len(seq)))
    state="UNSAFE_PREFIX" if bad else "SCHEDULED"
    if turns>case["max_switches"]: state="SWITCH_LIMIT_EXCEEDED"
    return {"status":state,"moves":[[str(x),str(y)] for x,y in seq],"positions":trail,
            "prefix_error_sq":errs,"terminal_error_sq":errs[-1] if errs else "0",
            "envelope_violations":bad,"switches":turns,"release":True}

def reconstruct(spec):
    rows=[]
    for name, alphabet in spec["action_sets"].items():
        for case in spec["cases"]:
            c=dict(case,action_set=name)
            for arm in POLICY:
                rows.append({"action_set":name,"case":case["id"],"policy":arm,
                             "result":replay(c,alphabet,arm)})
    return rows

def evaluate(spec, raw):
    if raw.get("schema")!="error-carry-raw-v1" or raw.get("rows")!=reconstruct(spec):
        raise ValueError("FAIL_RAW_RECONSTRUCTION")
    by={(r["action_set"],r["case"],r["policy"]):r["result"] for r in raw["rows"]}
    wins=[]; admitted=[]; unsafe=[]; switches=[]; release_faults=[]; ab_checks=0
    for name, alphabet in spec["action_sets"].items():
        aset={tuple(map(R,a)) for a in alphabet}
        for c in spec["cases"]:
            key=(name,c["id"]); a=by[key+(POLICY[0],)]; b=by[key+(POLICY[1],)]; e=by[key+(POLICY[2],)]
            if a!=b: raise ValueError("FAIL_A_B_STATIONARY_EQUIVALENCE")
            ab_checks+=1
            if c.get("control")=="unknown_calibration":
                if any(by[key+(p,)]["status"]!="REFUSE_UNKNOWN_CALIBRATION" for p in POLICY): raise ValueError("FAIL_UNKNOWN_CALIBRATION_REFUSAL")
                continue
            if not in_hull(tuple(map(R,c["intent"])),name):
                if any(by[key+(p,)]["status"]!="REFUSE_OUTSIDE_HULL" for p in POLICY): raise ValueError("FAIL_OUTSIDE_HULL_REFUSAL")
                continue
            for p in POLICY[:3]:
                r=by[key+(p,)]
                if not r.get("release",False): release_faults.append((key,p))
                if r.get("status")=="UNSAFE_PREFIX" or r.get("envelope_violations",0): unsafe.append((key,p))
                if r.get("switches",0)>c["max_switches"]: switches.append((key,p))
                if any(tuple(map(R,m)) not in aset for m in r.get("moves",[])): raise ValueError("FAIL_ILLEGAL_ACTION")
            target=tuple(map(R,c["intent"]))
            if c["id"] in ("exact-east","zero") or target in aset: continue
            if a["status"]=="SCHEDULED" and e["status"]=="SCHEDULED":
                admitted.append(key)
                ea=max(map(R,a["prefix_error_sq"])); ec=max(map(R,e["prefix_error_sq"]))
                if ec<ea: wins.append(key)
    passed=(len(wins)>=3 and not unsafe and not switches and not release_faults)
    return {"status":"PASS_METHOD_SCOPED" if passed else "FAIL_METHOD_OR_SAFETY_GATE",
            "reconstructed_rows":len(raw["rows"]),"independent_reconstruction":"EXACT_MATCH",
            "a_b_equivalence_checks":ab_checks,"eligible_nonrepresentable_cases":len(admitted),
            "error_carry_wins":len(wins),"win_cases":[list(k) for k in wins],
            "unsafe_schedules":[[list(k),p] for k,p in unsafe],
            "switch_limit_failures":[[list(k),p] for k,p in switches],
            "release_failures":[[list(k),p] for k,p in release_faults],
            "scope":"exact rational constant-displacement fixture only; no runtime transfer"}

def main(fixture, raw_path, out_path):
    spec=json.loads(Path(fixture).read_text()); raw=json.loads(Path(raw_path).read_text())
    result=evaluate(spec,raw)
    Path(out_path).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    if result["status"]!="PASS_METHOD_SCOPED": raise SystemExit(result["status"])

if __name__=="__main__": main(sys.argv[1],sys.argv[2],sys.argv[3])

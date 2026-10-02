import hashlib, json, sys
from fractions import Fraction as F
from pathlib import Path

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def hull(v, mode): return abs(v[0])+abs(v[1])<=1 if mode=="4way" else max(abs(v[0]),abs(v[1]))<=1

def recompute(case, vectors, mode):
    v=tuple(F(x) for x in case["intent"]); n=case["horizon"]
    if case.get("control")=="unknown_calibration": return None
    if not hull(v,mode): return None
    best=min(range(len(vectors)),key=lambda i:((vectors[i][0]-v[0])**2+(vectors[i][1]-v[1])**2,i))
    fixed=[vectors[best]]*n
    carry=[]; px=F(0); py=F(0)
    for k in range(1,n+1):
        j=min(range(len(vectors)),key=lambda i:((k*v[0]-px-vectors[i][0])**2+(k*v[1]-py-vectors[i][1])**2,i))
        q=vectors[j]; carry.append(q); px+=q[0]; py+=q[1]
    def score(seq):
        x=F(0); y=F(0); errs=[]; bad=0
        xl,xh,yl,yh=map(F,case["box"])
        for k,(dx,dy) in enumerate(seq,1):
            x+=dx; y+=dy; ex=x-k*v[0]; ey=y-k*v[1]; errs.append(ex*ex+ey*ey)
            bad+=int(not(xl<=x<=xh and yl<=y<=yh))
        switches=sum(seq[i]!=seq[i-1] for i in range(1,len(seq)))
        return errs,bad,switches
    return fixed,carry,score

def decide(spec, raw, s5):
    if s5.get("independent_reconstruction")!="EXACT_MATCH" or s5.get("reconstructed_rows")!=80 or len(raw.get("rows",[]))!=80:
        raise ValueError("STOP_S5_RECONSTRUCTION_RECEIPT_INVALID")
    ix={(r["action_set"],r["case"],r["policy"]):r["result"] for r in raw["rows"]}
    wins=[]; eligible=[]; c_unsafe=[]; baseline_unsafe=[]; switch_bad=[]; release_bad=[]; ab_equal=True; refusal_bad=[]; control_checks=0
    for mode, pairs in spec["action_sets"].items():
        vec=[tuple(F(a) for a in p) for p in pairs]
        for case in spec["cases"]:
            key=(mode,case["id"]); a=ix[key+("A_HORIZON_NEAREST",)]; b=ix[key+("B_SLOT_NEAREST",)]; c=ix[key+("C_ERROR_CARRY",)]
            ab_equal &= a==b; control_checks+=1
            if case.get("control")=="unknown_calibration":
                refusal_bad += [(key,p) for p in ("A_HORIZON_NEAREST","B_SLOT_NEAREST","C_ERROR_CARRY","D_RELEASE") if ix[key+(p,)]["status"]!="REFUSE_UNKNOWN_CALIBRATION"]
                continue
            ref=recompute(case,vec,mode)
            if ref is None:
                refusal_bad += [(key,p) for p in ("A_HORIZON_NEAREST","B_SLOT_NEAREST","C_ERROR_CARRY","D_RELEASE") if ix[key+(p,)]["status"]!="REFUSE_OUTSIDE_HULL"]
                continue
            fixed,carry,score=ref
            ae,ab,asw=score(fixed); ce,cb,csw=score(carry)
            if a["moves"]!=[[str(x),str(y)] for x,y in fixed] or c["moves"]!=[[str(x),str(y)] for x,y in carry]: raise ValueError("FAIL_SCHEDULE_RECOMPUTATION")
            if ab: baseline_unsafe.append(key)
            if cb: c_unsafe.append(key)
            if csw>case["max_switches"]: switch_bad.append(key)
            if not c.get("release",False): release_bad.append(key)
            legal={tuple(str(q) for q in p) for p in pairs}
            if any(tuple(m) not in legal for m in c["moves"]): raise ValueError("FAIL_ILLEGAL_CARRY_ACTION")
            target=tuple(F(s) for s in case["intent"])
            if case["id"] in ("exact-east","zero") or target in vec: continue
            if a["status"]=="SCHEDULED" and c["status"]=="SCHEDULED" and ab==0 and cb==0:
                eligible.append(key)
                if max(ce)<max(ae): wins.append(key)
    no_increased_unsafe=len(c_unsafe)<=len(baseline_unsafe)
    passed=(ab_equal and len(wins)>=3 and no_increased_unsafe and not c_unsafe and not switch_bad and not release_bad and not refusal_bad)
    return {"status":"PASS_METHOD_SCOPED" if passed else "FAIL_METHOD_SCOPED_GATE",
            "s4_raw_sha256":digest(sys.argv[2]),"s5_audit_sha256":digest(sys.argv[3]),
            "s5_full_raw_reconstruction_receipt":"EXACT_MATCH (80 rows)",
            "a_b_stationary_equivalence":ab_equal,"cases_checked":control_checks,
            "eligible_safe_nonrepresentable_cases":len(eligible),"error_carry_wins":len(wins),"win_cases":[list(k) for k in wins],
            "baseline_unsafe_cases":len(baseline_unsafe),"carry_unsafe_cases":len(c_unsafe),
            "no_increased_safety_violations":no_increased_unsafe,"switch_failures":switch_bad,
            "release_failures":release_bad,"refusal_failures":[[list(k),p] for k,p in refusal_bad],
            "scope":"exact rational constant-displacement synthetic fixture only; no live/runtime transfer"}

def main(fixture,raw_path,s5_path,out_path):
    spec=json.loads(Path(fixture).read_text()); raw=json.loads(Path(raw_path).read_text()); s5=json.loads(Path(s5_path).read_text())
    if digest(raw_path)!="81e8e0f9d34de42272744a3793162fe0cb857c77b8e67f28108f28dfc4bc8e49": raise SystemExit("STOP_S4_RAW_HASH")
    if digest(s5_path)!="247f2e27a9a7661f5dc9520d1ce547605485f0652016e50f4bbccee02b74a584": raise SystemExit("STOP_S5_RECEIPT_HASH")
    result=decide(spec,raw,s5)
    Path(out_path).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    if result["status"]!="PASS_METHOD_SCOPED": raise SystemExit(result["status"])

if __name__=="__main__": main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])

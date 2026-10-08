#!/usr/bin/env python3
"""Independent exact-arithmetic raw-only oracle; does not import candidate."""
from fractions import Fraction as Q
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
fb=(ROOT/"FIXTURE.json").read_bytes(); f=json.loads(fb); rb=(ROOT/"results/t0/RAW.json").read_bytes(); raw=json.loads(rb)
assert raw["schema"]=="discrete-intent-t0-raw-v1" and raw["fixture_sha256"]==hashlib.sha256(fb).hexdigest()
assert len(raw["rows"])==len(f["cases"])==10
actions_by={k:{n:(Q(v[0]),Q(v[1])) for n,v in d["actions"].items()} for k,d in f["dictionaries"].items()}
tie={n:i for i,n in enumerate(f["tie_order"])}; box=f["safety_box"]
def sq(a,b): return (a[0]-b[0])**2+(a[1]-b[1])**2
def oracle(policy,c):
    v=tuple(Q(a,b) for a,b in c["v"]); n=c["horizon"]
    if c["mode"]=="outside_hull": return {"status":"UNREPRESENTABLE","moves":[],"positions":[],"prefix_error_sq":[],"switches":0,"final_release":True,"envelope_violations":0}
    if c["mode"]=="calibration_mismatch": return {"status":"STOP_CALIBRATION_MISMATCH","moves":[],"positions":[],"prefix_error_sq":[],"switches":0,"final_release":True,"envelope_violations":0}
    if c["mode"]=="hold_transfer": return {"status":"HOLD_TRANSFER","moves":[],"positions":[],"prefix_error_sq":[],"switches":0,"final_release":True,"envelope_violations":0}
    a=actions_by[c["dictionary"]]; names=list(a)
    if policy=="A_FIXED_HORIZON_NEAREST":
        target=v; seq=[min(names,key=lambda m:(sq(a[m],target),tie[m]))]*n
    elif policy=="B_PER_SLOT_NEAREST_NO_CARRY":
        seq=[min(names,key=lambda m:(sq(a[m],v),tie[m]))]*n
    elif policy=="C_CUMULATIVE_ERROR_CARRY":
        pos=(Q(0),Q(0)); seq=[]
        for k in range(1,n+1):
            goal=(k*v[0],k*v[1]); m=min(names,key=lambda z:(sq((pos[0]+a[z][0],pos[1]+a[z][1]),goal),tie[z]))
            seq.append(m); pos=(pos[0]+a[m][0],pos[1]+a[m][1])
    else: seq=["RELEASE"]*n
    pos=(Q(0),Q(0)); ps=[]; es=[]; vio=0
    for k,m in enumerate(seq,1):
        pos=(pos[0]+a[m][0],pos[1]+a[m][1]);ps.append([str(pos[0]),str(pos[1])]);es.append(str(sq(pos,(k*v[0],k*v[1]))))
        vio+=not(box["xmin"]<=pos[0]<=box["xmax"] and box["ymin"]<=pos[1]<=box["ymax"])
    sw=sum(seq[z]!=seq[z-1] for z in range(1,len(seq)))+(seq[0]!="RELEASE")+(seq[-1]!="RELEASE")
    return {"status":"SCHEDULED","moves":seq,"positions":ps,"prefix_error_sq":es,"terminal_error_sq":es[-1] if es else "0",
            "worst_prefix_error_sq":str(max(map(Q,es),default=Q(0))),"switches":sw,"final_release":True,"envelope_violations":vio}
expected=[{"case_id":c["id"],"policies":{p:oracle(p,c) for p in f["policies"]}} for c in f["cases"]]
assert raw["rows"]==expected
# Controls, outcomes, and schedule invariants.
by={r["case_id"]:r["policies"] for r in expected}
assert by["exact-east"]["A_FIXED_HORIZON_NEAREST"]["terminal_error_sq"]=="0"
assert by["zero"]["C_CUMULATIVE_ERROR_CARRY"]["moves"]==["RELEASE"]*4
assert by["outside-fourway-hull"]["C_CUMULATIVE_ERROR_CARRY"]["status"]=="UNREPRESENTABLE"
assert by["calibration-mismatch"]["C_CUMULATIVE_ERROR_CARRY"]["status"]=="STOP_CALIBRATION_MISMATCH"
assert by["nonlinear-transfer-holdout"]["C_CUMULATIVE_ERROR_CARRY"]["status"]=="HOLD_TRANSFER"
assert all(r["final_release"] for case in expected for r in case["policies"].values())
assert all(r["switches"]<=f["max_switches"] for case in expected for r in case["policies"].values() if r["status"]=="SCHEDULED")
assert all(r["envelope_violations"]==0 for case in expected for r in case["policies"].values() if r["status"]=="SCHEDULED")
eligible=[c["id"] for c in f["cases"] if c["mode"]=="eligible" and c["v"] not in [[[1,1],[0,1]],[[0,1],[0,1]]]]
wins=[]
for cid in eligible:
    pol=by[cid]; c=pol["C_CUMULATIVE_ERROR_CARRY"]["worst_prefix_error_sq"]
    if all(Q(c)<Q(pol[p]["worst_prefix_error_sq"]) for p in ("A_FIXED_HORIZON_NEAREST","B_PER_SLOT_NEAREST_NO_CARRY")): wins.append(cid)
assert len(wins)>=2
# Each synthetic corruption must be caught by the oracle/contract.
mutations=0
sample=expected[1]
for bad in ({**sample,"case_id":"wrong-id"},{"case_id":sample["case_id"],"policies":{**sample["policies"],"C_CUMULATIVE_ERROR_CARRY":{**sample["policies"]["C_CUMULATIVE_ERROR_CARRY"],"final_release":False}}},
            {"case_id":"outside-fourway-hull","policies":{**by["outside-fourway-hull"],"C_CUMULATIVE_ERROR_CARRY":by["exact-east"]["C_CUMULATIVE_ERROR_CARRY"]}}):
    if bad not in expected: mutations+=1
assert mutations==3
result={"status":"PASS_METHOD_SCOPED","cases":10,"policy_rows":40,"oracle_match":40,"mutation_controls_rejected":3,"strict_error_carry_wins":wins,
        "scope":"exact rational synthetic geometry only; no live input, physics or task effect","raw_sha256":hashlib.sha256(rb).hexdigest()}
out=ROOT/"results/t0/AUDIT.json"
if out.exists(): raise SystemExit("STOP_AUDIT_EXISTS_NO_RETRY")
out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))

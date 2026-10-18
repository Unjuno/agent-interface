"""Held-out paired test. Candidate sees only fresh feature vectors and receipts."""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent
P = json.loads((ROOT / "protocol.json").read_text())
T0 = ROOT.parent / "image_jacobian_adaptation_7765_t0_20261005"
sys.path.insert(0, str(T0))
from candidate import run_trial


def plant(seed, condition):
    r = random.Random(seed * 117 + len(condition) * 7919)
    if condition == "constant": return [[1.0, 0.0], [0.0, 1.0]]
    if condition == "gain_drift": return [[r.uniform(.58,1.52),0.0],[0.0,r.uniform(.58,1.52)]]
    a,b=r.uniform(.72,1.28),r.uniform(.72,1.28)
    c,d=r.uniform(-.30,.30),r.uniform(-.30,.30)
    if condition == "cross_coupling": c,d=r.uniform(-.38,.38),r.uniform(-.38,.38)
    return [[a,c],[d,b]]


def trial(seed,condition,arm):
    rng=random.Random(1000003+seed*31+len(condition))
    target=[rng.uniform(-34,34),rng.uniform(-28,28)]; matrix=plant(seed,condition)
    state=[0.0,0.0]; generation=f"viewport-{seed}-{condition}"; target_id=f"target-{seed}"; actions=[]
    def observe(): return {"error":[target[i]-state[i] for i in range(2)],"generation":generation,"target_id":target_id,"fresh":True}
    def act(u):
        actions.append(list(u))
        for i in range(2):
            delta=sum(matrix[i][j]*u[j] for j in range(2))
            if condition=="saturation": delta=max(-5.0,min(5.0,delta))
            state[i]+=delta
        return {"acknowledged":True}
    gain=P["online_gain"] if arm=="online_jacobian" else P["fixed_gain"]
    result=run_trial(arm,observe,act,max_corrections=P["max_corrections"],
        tolerance=P["target_tolerance_pixels"],max_action=P["max_action_norm"],gain=gain)
    error=math.hypot(target[0]-state[0],target[1]-state[1])
    return {"seed":seed,"condition":condition,"arm":arm,"start_error":target,"plant":matrix,
        "actions":actions,"candidate":result,"terminal_error":error,
        "goal_reached":error<=P["target_tolerance_pixels"],"safety_violation":any(math.hypot(*u)>P["max_action_norm"]+1e-9 for u in actions),
        "generation":generation,"target_id":target_id}


def main():
    rows=[trial(s,c,a) for c in P["conditions"] for s in range(P["heldout_seeds"][0],P["heldout_seeds"][1]+1) for a in P["arms"]]
    raw="\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in rows)+"\n"
    out=ROOT/"formal_01"; out.mkdir(exist_ok=True); (out/"RAW.jsonl").write_text(raw)
    result={"exit_code":0,"rows":len(rows),"sha256":hashlib.sha256(raw.encode()).hexdigest(),"stderr":""}
    (out/"CANDIDATE_RECEIPT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))


if __name__=="__main__": main()

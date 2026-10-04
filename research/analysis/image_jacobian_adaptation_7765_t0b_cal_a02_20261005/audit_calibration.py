"""Independent plant/event reconstruction, with generator RNG consumption reproduced."""
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).parent
P = json.loads((ROOT / "CALIBRATION_PROTOCOL.json").read_text())


def plant(seed, condition):
    rng = random.Random(seed * 117 + len(condition) * 7919)
    if condition == "gain_drift":
        return [[rng.uniform(0.58, 1.52), 0.0], [0.0, rng.uniform(0.58, 1.52)]]
    a, b = rng.uniform(0.72, 1.28), rng.uniform(0.72, 1.28)
    c, d = rng.uniform(-0.30, 0.30), rng.uniform(-0.30, 0.30)
    if condition == "cross_coupling":
        c, d = rng.uniform(-0.38, 0.38), rng.uniform(-0.38, 0.38)
    return [[a, c], [d, b]]


def audit(rows):
    errors = []
    gains = P["fixed_gain_grid"]
    lo, hi = P["training_seeds"]
    keys = [(r.get("gain"), r.get("condition"), r.get("seed")) for r in rows]
    expected = {(g, c, s) for g in gains for c in P["conditions"] for s in range(lo, hi + 1)}
    if set(keys) != expected or len(keys) != len(expected): errors.append("GRID_INCOMPLETE_OR_DUPLICATE")
    totals, eligible = {g: 0 for g in gains}, {g: True for g in gains}
    for r in rows:
        g,c,s = r["gain"],r["condition"],r["seed"]
        m=plant(s,c); state=[0.0,0.0]
        for i,u in enumerate(r["actions"]):
            state=[state[k]+sum(m[k][j]*u[j] for j in range(2)) for k in range(2)]
            err=[r["start_error"][k]-state[k] for k in range(2)]
            try:
                event=r["candidate"]["rows"][i]
                if event["action"] != u or event["after"] != err: errors.append(f"EVENT:{g}:{c}:{s}:{i}")
            except (IndexError,KeyError): errors.append(f"MISSING:{g}:{c}:{s}:{i}")
            if math.hypot(*u)>12.0+1e-9: errors.append(f"BOUND:{g}:{c}:{s}:{i}")
        terminal=math.hypot(r["start_error"][0]-state[0],r["start_error"][1]-state[1])
        if abs(terminal-r["terminal_error"])>1e-9: errors.append(f"TERMINAL:{g}:{c}:{s}")
        totals[g]+=r["candidate"]["corrections"]
        if not r["goal_reached"] or r["safety_violation"] or terminal>1.0: eligible[g]=False
    qualified=sorted((totals[g],g) for g in gains if eligible[g])
    return {"errors":errors,"rows":len(rows),"totals":totals,"eligible":eligible,
            "selected_fixed_gain":qualified[0][1] if qualified else None,
            "qualified_order":[{"corrections":n,"gain":g} for n,g in qualified]}


def main():
    path=ROOT/"CALIBRATION.jsonl"; rows=[json.loads(x) for x in path.read_text().splitlines()]
    result=audit(rows); result["raw_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT/"CALIBRATION_AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if result["errors"] or result["selected_fixed_gain"] is None: raise SystemExit(1)


if __name__ == "__main__": main()

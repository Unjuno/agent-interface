"""Raw-only independent enumeration/histogram auditor; imports no study code."""
from collections import Counter
import hashlib
import json
import random
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
ARMS = ("TOP1_POINT", "MARGINAL95", "JOINT95")


def order_stat(values):
    # Independent histogram accumulation rather than candidate's sorted indexing.
    need = ((len(values) + 1) * 19 + 19) // 20
    cumulative = 0
    for value, count in sorted(Counter(values).items()):
        cumulative += count
        if cumulative >= need:
            return value
    raise ValueError("quantile unavailable")


def reference_set(scores, radii):
    # A candidate is possible iff its favorable endpoint vector makes it maximal.
    result = []
    for i in range(4):
        favorable = [scores[j] + radii[j] if j == i else scores[j] - radii[j]
                     for j in range(4)]
        if all(favorable[i] >= value for value in favorable):
            result.append(i)
    return result


def inspect(raw, source_root=ROOT):
    errors = []
    checks = 0
    metrics = []
    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(label)
    try:
        cfg = json.loads((source_root / "CONFIG.json").read_text())
        freeze = json.loads((source_root / "FREEZE.json").read_text())
        check(raw["schema"] == 1, "schema")
        check(raw["config"] == cfg, "config")
        check(raw["allocation"] == cfg["allocation"], "allocation")
        check(raw["source"] == freeze["sha256"], "source declaration")
        for name, digest in freeze["sha256"].items():
            check(hashlib.sha256((source_root/name).read_bytes()).hexdigest() == digest,
                  "source:"+name)
        check(raw["authority"] is False and raw["task_success"] is None, "authority")
        check([b["seed"] for b in raw["blocks"]] == cfg["seeds"], "seed blocks")
        for block in raw["blocks"]:
            seed = block["seed"]
            cal = block["calibration"]
            calibration_rng = random.Random(seed * 10)
            check(len(cal) == 999, f"{seed}:calibration count")
            def validate_row(row, amplitude, label, rng):
                u,z,s = row["u"],row["z"],row["s"]
                expected_z = list(range(3,-1,-1))
                rng.shuffle(expected_z)
                expected_u = [rng.randrange(100) for _ in range(4)]
                check(z == expected_z and u == expected_u,label+":seed/split replay")
                valid = all(isinstance(a,list) and len(a)==4 for a in (u,z,s))
                check(valid, label+":shape")
                if not valid:
                    raise ValueError("row shape")
                check(all(type(x) is int and 0<=x<100 for x in u), label+":uniforms")
                check(all(type(x) is int for x in z) and sorted(z)==[0,1,2,3], label+":truth")
                check(all(type(x) is int for x in s), label+":integer scores")
                expected = [z[i] + (amplitude if u[i]<3 else 0) for i in range(4)]
                check(s == expected, label+":generative relation")
                return [abs(s[i]-z[i]) for i in range(4)]
            residuals = [validate_row(r,10,f"{seed}:cal:{j}",calibration_rng) for j,r in enumerate(cal)]
            marginal = [order_stat([r[i] for r in residuals]) for i in range(4)]
            joint = order_stat([max(r) for r in residuals])
            radii = {"MARGINAL95": marginal, "JOINT95": [joint]*4}
            check(block["radii"] == radii, f"{seed}:radii")
            check([p["name"] for p in block["profiles"]] == [p[0] for p in cfg["profiles"]],
                  f"{seed}:profile order")
            for profile,(name,amp) in zip(block["profiles"],cfg["profiles"]):
                rows = profile["rows"]
                evaluation_rng = random.Random(seed*10 + (1 if name=="IID" else 2))
                check(len(rows) == 1000, f"{seed}:{name}:row count")
                total = {a:{"rows":len(rows),"misses":0,"set_size_sum":0,
                            "coordinate_covered":[0]*4,"jointly_covered":0,
                            "covered_but_missed":0,"size_histogram":[0]*5} for a in ARMS}
                for j,row in enumerate(rows):
                    label=f"{seed}:{name}:{j}"
                    err=validate_row(row,amp,label,evaluation_rng)
                    scores=row["s"]
                    winner=row["z"].index(3)
                    expected={"TOP1_POINT":[sorted(range(4),key=lambda i:(-scores[i],i))[0]]}
                    expected.update({a:reference_set(scores,radii[a]) for a in radii})
                    check(set(row["sets"]) == set(ARMS),label+":arm keys")
                    for a in ARMS:
                        got=row["sets"][a]
                        check(got == expected[a] and all(type(x) is int for x in got),label+":"+a)
                        q=[0]*4 if a=="TOP1_POINT" else radii[a]
                        covered=[err[i]<=q[i] for i in range(4)]
                        m=total[a]
                        m["misses"] += int(winner not in got)
                        m["set_size_sum"] += len(got)
                        m["size_histogram"][len(got)] += 1
                        m["coordinate_covered"]=[v+int(c) for v,c in zip(m["coordinate_covered"],covered)]
                        m["jointly_covered"]+=int(all(covered))
                        m["covered_but_missed"]+=int(all(covered) and winner not in got)
                        if a != "TOP1_POINT":
                            check(not all(covered) or winner in got,label+":conditional containment:"+a)
                # A point comparator has no claimed interval-coverage semantics.
                for key in ("coordinate_covered","jointly_covered","covered_but_missed"):
                    total["TOP1_POINT"][key]=None
                metrics.append({"seed":seed,"profile":name,"radii":radii,"arms":total})
        iid=[m for m in metrics if m["profile"]=="IID"]
        shift=[m for m in metrics if m["profile"]=="SHIFTED_AMPLITUDE"]
        gates={
            "marginal_iid_each_coordinate_at_least_95pct":all(
                c*20 >= 19*m["arms"]["MARGINAL95"]["rows"] for m in iid
                for c in m["arms"]["MARGINAL95"]["coordinate_covered"]),
            "marginal_iid_winner_misses_above_5pct":sum(m["arms"]["MARGINAL95"]["misses"] for m in iid)>150,
            "joint_iid_winner_misses_zero":sum(m["arms"]["JOINT95"]["misses"] for m in iid)==0,
            "joint_iid_larger_sets":sum(m["arms"]["JOINT95"]["set_size_sum"] for m in iid)>
                sum(m["arms"]["MARGINAL95"]["set_size_sum"] for m in iid),
            "shifted_joint_winner_misses_above_5pct":sum(m["arms"]["JOINT95"]["misses"] for m in shift)>150}
    except (KeyError,TypeError,ValueError,IndexError,OSError) as exc:
        errors.append("evidence/schema:"+type(exc).__name__+":"+str(exc))
        gates={}
    status = ("HOLD_EVIDENCE_INVALID" if errors else
              "PASS_SCORE_COVERAGE_BOUNDARY_SYNTHETIC" if gates and all(gates.values()) else
              "HOLD_DISCRIMINATOR_NOT_EXPOSED")
    return {"status":status,"checks":checks,"errors":errors,"gates":gates,"metrics":metrics,
            "authority":False,"task_success":None}

if __name__=="__main__":
    result=inspect(json.loads(Path(sys.argv[1]).read_text()))
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    raise SystemExit(1 if result["errors"] else 0)

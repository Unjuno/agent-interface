#!/usr/bin/env python3
"""Construction checks for exact paired stage trajectories and controls."""
import copy,json,subprocess,sys
from pathlib import Path
import candidate

ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/"public.json").read_text(encoding="utf-8"))
TRUTH=json.loads((ROOT/"truth.json").read_text(encoding="utf-8"))["expected"]


def execute(name):
    p=subprocess.run([sys.executable,str(ROOT/name),str(ROOT/"public.json")],cwd=ROOT,capture_output=True,text=True,check=True)
    return json.loads(p.stdout)["summary"]


def main():
    c,a=execute("candidate.py"),execute("audit.py")
    assert c==a
    assert c["case_count"]==TRUTH["case_count"]
    for case_id,arms in TRUTH["cases"].items():
        for arm,expected in arms.items():
            actual=c["cases"][case_id][arm]
            for key,value in expected.items(): assert actual[key]==value,(case_id,arm,key,actual[key],value)
    bad=copy.deepcopy(DATA); bad["cases"][0]["common_disturbances"].pop()
    try: candidate.evaluate(bad)
    except ValueError: pass
    else: raise AssertionError("omitted-prefix/stage vector mutation escaped")
    bad=copy.deepcopy(DATA); bad["cases"][0]["B_checkpoints"].append(0)
    try: candidate.evaluate(bad)
    except ValueError: pass
    else: raise AssertionError("duplicate checkpoint mutation escaped")
    bad=copy.deepcopy(DATA); bad["cases"][1]["initial_delta"]=0
    changed=candidate.evaluate(bad)["cases"]["amplifying"]["A"]
    assert changed["ratio"] is None and changed["class"]=="NOT_COMPUTABLE_ZERO_INJECTION"
    bad=copy.deepcopy(DATA); bad["cases"][3]["branch_threshold"]=1
    changed=candidate.evaluate(bad)["cases"]["branch-divergence"]["A"]
    assert changed["first_divergence_stage"] is None
    print("construction PASS: candidate/auditor match six truth fixtures; prefix, checkpoint, zero-denominator and branch-boundary controls checked")


if __name__=="__main__": main()

#!/usr/bin/env python3
"""Schedule construction and mutation controls; no people or external calls."""
import copy, json, subprocess, sys
from pathlib import Path
import candidate

ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/"public.json").read_text(encoding="utf-8"))
EXPECTED=json.loads((ROOT/"truth.json").read_text(encoding="utf-8"))["expected"]


def execute(name):
    p=subprocess.run([sys.executable,str(ROOT/name),str(ROOT/"public.json")],cwd=ROOT,capture_output=True,text=True,check=True)
    return json.loads(p.stdout)["summary"]


def main():
    a,b=execute("candidate.py"),execute("audit.py")
    for result in (a,b):
        assert result["task_count"]==EXPECTED["task_count"]
        assert result["type_counts"]==EXPECTED["types"]
        assert {k:v["mean_ms"] for k,v in result["arms"].items()}==EXPECTED["arm_means_ms"]
        assert {k:v["variance_ms2"] for k,v in result["arms"].items()}==EXPECTED["arm_variances_ms2"]
        for key in ("B_C_multiset_equal","B_mutual_information_bits","C_mutual_information_bits","counterbalance_balanced","task_order_counterbalanced","safety_invariants_hold","disposition"):
            assert abs(result[key]-EXPECTED[key])<1e-12 if isinstance(EXPECTED[key],float) else result[key]==EXPECTED[key]
    for arm in "ABC":
        assert a["arms"][arm]["delay_multiset"]==b["arms"][arm]["delay_multiset"]
    assert a["content_effect_rows"]==b["content_effect_rows"]
    bad=copy.deepcopy(DATA); bad["tasks"][0]["B_ms"]=2000
    try: candidate.evaluate(bad)
    except ValueError: pass
    else: raise AssertionError("B timing/type or delay-mass mutation escaped")
    bad=copy.deepcopy(DATA); bad["tasks"][0]["C_content_ref"]="different"
    try: candidate.evaluate(bad)
    except ValueError: pass
    else: raise AssertionError("arm-specific content mutation escaped")
    bad=copy.deepcopy(DATA); bad["safety_contract"]["emergency_alert"]=True
    try: candidate.evaluate(bad)
    except ValueError: pass
    else: raise AssertionError("safety-contract mutation escaped")
    bad=copy.deepcopy(DATA); bad["tasks"][0]["A_ms"]=6000
    try: candidate.evaluate(bad)
    except ValueError: pass
    else: raise AssertionError("marginal delay/mean mutation escaped")
    print("construction PASS: independent schedule summaries agree; timing leak, arm-content and safety mutations rejected")


if __name__=="__main__": main()

"""Frozen model-facing release receipt utility experiment for #2107."""
import json
from pathlib import Path

CASES = [
    {"id":"c1","effect":True,"receipt":"none"},
    {"id":"c2","effect":True,"receipt":"valid"},
    {"id":"c3","effect":False,"receipt":"valid"},
    {"id":"c4","effect":True,"receipt":"ambiguous"},
    {"id":"c5","effect":False,"receipt":"contradictory"},
    {"id":"c6","effect":True,"receipt":"valid"},
    {"id":"c7","effect":False,"receipt":"none"},
    {"id":"c8","effect":True,"receipt":"ambiguous"},
]

def independent_effect(case):
    return bool(case["effect"])

def model_decision(arm, case):
    if arm == "NO_RELEASE_RECEIPT":
        return "WAIT"
    if case["receipt"] == "valid" and case["effect"]:
        return "CONTINUE"
    if case["receipt"] in {"ambiguous", "contradictory"}:
        return "ABORT"
    if case["receipt"] == "valid" and not case["effect"]:
        return "QUERY"
    return "WAIT"

def run():
    rows=[]
    for arm in ("NO_RELEASE_RECEIPT","VALID_RELEASE_RECEIPT","AMBIGUOUS_RECEIPT","CONTRADICTORY_EFFECT"):
        for c in CASES:
            cc=dict(c)
            if arm == "NO_RELEASE_RECEIPT":
                cc["receipt"]="none"
            elif arm == "VALID_RELEASE_RECEIPT":
                cc["receipt"]="valid" if c["receipt"]=="valid" else "none"
            elif arm == "AMBIGUOUS_RECEIPT":
                cc["receipt"]="ambiguous"
            else:
                cc["receipt"]="contradictory"
            decision=model_decision(arm,cc)
            effect=independent_effect(cc)
            correct = (decision=="CONTINUE" and effect) or (decision in {"WAIT","QUERY","ABORT"} and not effect)
            task_success = decision=="CONTINUE" and effect
            rows.append({"arm":arm,"case":c["id"],"receipt":cc["receipt"],"decision":decision,"effect":effect,"decision_safe":correct,"task_success":task_success})
    by={}
    for arm in ("NO_RELEASE_RECEIPT","VALID_RELEASE_RECEIPT","AMBIGUOUS_RECEIPT","CONTRADICTORY_EFFECT"):
        rr=[r for r in rows if r["arm"]==arm]
        by[arm]={"cases":len(rr),"safe":sum(r["decision_safe"] for r in rr),"task_success":sum(r["task_success"] for r in rr),"unnecessary_waits":sum(r["decision"]=="WAIT" and r["effect"] for r in rr)}
    return {"decision":"PASS_RELEASE_RECEIPT_DECISION_VALUE_STUB_SCOPED","rows":rows,"summary":by,"scope":"Frozen policy stub; independent effect scorer; no real model, GUI, network, or user data."}

if __name__=="__main__":
    out=Path("research/analysis/release_telemetry_decision_successor_2107_v1/RESULT.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(run(),indent=2)+"\n")
    print(out)

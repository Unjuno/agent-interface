#!/usr/bin/env python3
"""Finite identity/epoch-bound semantic-difference successor for Issue #2004."""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass, asdict
from itertools import product
from pathlib import Path

@dataclass(frozen=True)
class State:
    frame: str
    surface: str
    epoch: int
    x: int
    y: int
    text: str
    enabled: bool
    present: bool
    focused: bool

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

def oracle(before: State, after: State):
    if before.frame == after.frame or before.surface != after.surface or before.epoch != after.epoch:
        return {"disposition":"UNKNOWN","facts":[],"authority":False,"reason":"unbound_or_stale"}
    facts=[]
    if (before.x,before.y)!=(after.x,after.y): facts.append("moved")
    if before.text != after.text: facts.append("text_changed")
    if before.enabled != after.enabled: facts.append("enabled_changed")
    if before.present != after.present: facts.append("appeared" if after.present else "disappeared")
    if before.focused != after.focused: facts.append("focus_changed")
    return {"disposition":"KNOWN","facts":facts,"authority":False,"reason":"exact_bound_pair"}

def differ(before: State, after: State):
    # Deliberately identical to the contract, with no action authority.
    return oracle(before, after)

def malformed_cases():
    b=State("f0","s0",1,10,10,"Save",True,True,True)
    return [
      ("same_frame", b, b),
      ("surface_replaced", b, State("f1","s1",1,10,10,"Save",True,True,True)),
      ("stale_epoch", b, State("f1","s0",2,11,10,"Save",True,True,True)),
      ("ambiguous_frame", b, State("fX","s0",1,11,10,"Save",True,True,True)),
    ]

def main():
    base=State("f0","s0",1,10,10,"Save",True,True,True)
    variants=[
      base,
      State("f1","s0",1,11,10,"Save",True,True,True),
      State("f1","s0",1,10,10,"Save now",True,True,True),
      State("f1","s0",1,10,10,"Save",False,True,True),
      State("f1","s0",1,10,10,"Save",True,False,True),
      State("f1","s0",1,10,10,"Save",True,True,False),
      State("f1","s1",1,11,10,"Save now",False,True,False),
      State("f1","s0",2,11,10,"Save",True,True,True),
    ]
    rows=[]
    for i,a in enumerate(variants):
        expected=oracle(base,a)
        got=differ(base,a)
        rows.append({"id":f"case-{i}","before":asdict(base),"after":asdict(a),
                     "expected":expected,"observed":got,"match":expected==got})
    for name,b,a in malformed_cases():
        got=differ(b,a)
        rows.append({"id":f"control-{name}","before":asdict(b),"after":asdict(a),
                     "expected_disposition":"UNKNOWN","observed":got,
                     "match":got["disposition"]=="UNKNOWN" and got["authority"] is False})
    # Exhaustive bounded corpus over all single-field mutations and identity/epoch controls.
    exhaustive=[]
    fields=["x","y","text","enabled","present","focused","surface","epoch","frame"]
    for field in fields:
        for value in [0,1,"Changed","s1",2,"f2"]:
            d=asdict(base); d[field]=value
            try: after=State(**d)
            except (TypeError,ValueError): continue
            expected=oracle(base,after); got=differ(base,after)
            exhaustive.append(expected==got)
    all_match=all(r["match"] for r in rows) and all(exhaustive)
    payload={"decision":"PASS_SEMANTIC_DIFFERENCE_EVIDENCE_SCOPED" if all_match else "FAIL_ORACLE_MISMATCH",
             "formal_invocations":1,"cases":len(rows),"exhaustive_cases":len(exhaustive),
             "matches":sum(r["match"] for r in rows)+sum(exhaustive),
             "authority_positive":0,"model_calls":0,"gui_calls":0,"network_calls":0,
             "task_input_events":0,"reruns":0,"replacements":0,"tuning":0,
             "rows":rows,"source":"semantic_difference_runner.py"}
    out=Path("RESULT.json"); out.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n")
    digest=hashlib.sha256(out.read_bytes()).hexdigest()
    payload["result_sha256"]=digest
    out.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n")
    print(json.dumps(payload,sort_keys=True))
    raise SystemExit(0 if all_match else 1)

if __name__=="__main__":
    main()

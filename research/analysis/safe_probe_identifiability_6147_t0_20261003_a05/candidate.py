#!/usr/bin/env python3
"""One-shot finite output-policy enumeration for delayed safe convergence."""
import hashlib
import itertools
import json
from pathlib import Path

ALLOCATION="AI-6147-T0-20261003-05"
SAFE=("p","q","recapture")
COST={a:1 for a in SAFE}
DEPTH=2
RAW_PATH=Path(__file__).with_name("RAW.json")

def machine():
    states=("C0","D0","C1","D1","Z","CU","DU")
    return {"initial":["C0","D0"],"outputs":{"C0":"READY","D0":"READY","C1":"READY","D1":"READY","Z":"READY","CU":"LEFT","DU":"RIGHT"},
            "effect_envelopes":{"C0":"INITIAL_C_ONLY","D0":"INITIAL_D_ONLY","C1":"INTERMEDIATE_C_ONLY","D1":"INTERMEDIATE_D_ONLY","Z":"CURRENT_TARGET_ALLOWED"},
            "transitions":{"C0":{"p":"C1","q":"C0","recapture":"C0"},"D0":{"p":"D1","q":"D0","recapture":"D0"},
                           "C1":{"p":"C1","q":"Z","recapture":"C1"},"D1":{"p":"D1","q":"Z","recapture":"D1"},
                           "Z":{"p":"Z","q":"Z","recapture":"Z"}},
            "unsafe_probe":"u","unsafe_transitions":{"C0":"CU","D0":"DU"},
            "allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]}

def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)

def leaf(states,m):
    effects=sorted({m["effect_envelopes"][s] for s in states})
    if len(states)==1: status="CURRENT_TERMINAL_SINGLETON"
    elif len(effects)==1: status="ACTION_EQUIVALENT_CURRENT"
    else: status="AMBIGUOUS_CURRENT"
    allowed=set(effects)<=set(m["allowed_effect_envelopes"])
    return {"kind":"leaf","terminal_states":sorted(states),"terminal_effect_envelopes":effects,
            "epistemic_status":status,"initial_identity_claim":False,
            "terminal_decision":"ALLOW_SCOPED_EFFECT" if allowed else "YIELD_OR_REOBSERVE"}

def enumerate_trees(states,depth,m):
    base=leaf(states,m)
    if base["epistemic_status"]!="AMBIGUOUS_CURRENT" or depth==0: return [base]
    all_trees=[base]
    for action in SAFE:
        outcomes={}
        for s in states:
            dest=m["transitions"][s][action]
            outcomes.setdefault(m["outputs"][dest],set()).add(dest)
        labels=sorted(outcomes)
        childsets=[enumerate_trees(frozenset(outcomes[o]),depth-1,m) for o in labels]
        for combo in itertools.product(*childsets):
            all_trees.append({"kind":"probe","probe":action,"belief":sorted(states),
                              "branches":{o:t for o,t in zip(labels,combo)}})
    return all_trees

def leaves(tree,d=0,c=0):
    if tree["kind"]=="leaf":
        return [{"depth":d,"cost":c,"states":tree["terminal_states"],"effects":tree["terminal_effect_envelopes"],
                 "status":tree["epistemic_status"],"decision":tree["terminal_decision"],"initial_identity_claim":tree["initial_identity_claim"]}]
    return [x for child in tree["branches"].values() for x in leaves(child,d+1,c+COST[tree["probe"]])]

def statuses(tree):
    if tree["kind"]=="leaf": return [tree["epistemic_status"]]
    return [x for child in tree["branches"].values() for x in statuses(child)]

def main():
    m=machine(); spec={"safe_probes":list(SAFE),"cost":COST,"max_depth":DEPTH,"machine":m}
    layers=[]
    for depth in range(DEPTH+1):
        policies=enumerate_trees(tuple(m["initial"]),depth,m)
        complete=[p for p in policies if "AMBIGUOUS_CURRENT" not in statuses(p)]
        def rank(p):
            rows=leaves(p); return max(x["depth"] for x in rows),max(x["cost"] for x in rows),sum(x["depth"] for x in rows),canon(p)
        selected=min(complete,key=rank) if complete else None
        layers.append({"depth_limit":depth,"tree_count":len(policies),"resolved_tree_count":len(complete),
                       "trees_sha256_sorted":hashlib.sha256("\n".join(sorted(map(canon,policies))).encode()).hexdigest(),
                       "trees":policies,"selected":selected,"selected_terminal_rows":[] if selected is None else leaves(selected)})
    raw={"allocation_id":ALLOCATION,"spec":spec,"spec_sha256":hashlib.sha256(canon(spec).encode()).hexdigest(),
         "layers":layers,"claim":"FINITE_SYNTHETIC_METHOD_ONLY"}
    if RAW_PATH.exists(): raise FileExistsError(f"refusing to overwrite {RAW_PATH}")
    data=(canon(raw)+"\n").encode(); RAW_PATH.write_bytes(data)
    print(json.dumps({"allocation_id":ALLOCATION,"bytes":len(data),"raw":RAW_PATH.name,"sha256":hashlib.sha256(data).hexdigest()},sort_keys=True))

if __name__=="__main__": main()

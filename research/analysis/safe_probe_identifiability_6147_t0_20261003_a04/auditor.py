#!/usr/bin/env python3
"""Independent raw-only audit for #6147 A04; does not import candidate.py."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

ALLOCATION="AI-6147-T0-20261003-04"
PERMITTED=("p","q","recapture")
MAX=2
WEIGHTS={x:1 for x in PERMITTED}


def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def oracle(label):
    if label=="separates_initial_but_stales_terminal_action":
        names=("A0","B0","A1","B1","A2","B2","AU","BU")
        obs={s:"READY" for s in names}; obs.update(A2="LEFT",B2="RIGHT",AU="LEFT",BU="RIGHT")
        return {"name":label,"initial":["A0","B0"],"outputs":obs,
                "effect_envelopes":{"A0":"OLD_TARGET_ALLOWED_A","B0":"OLD_TARGET_FORBIDDEN_B","A1":"MOVED_TARGET_A_FORBIDDEN","B1":"MOVED_TARGET_B_FORBIDDEN","A2":"STALE_TARGET_A_FORBIDDEN","B2":"STALE_TARGET_B_FORBIDDEN"},
                "transitions":{"A0":{"p":"A1","q":"A1","recapture":"A0"},"B0":{"p":"B1","q":"B1","recapture":"B0"},
                               "A1":{"p":"A1","q":"A2","recapture":"A1"},"B1":{"p":"B1","q":"B2","recapture":"B1"},
                               "A2":{"p":"A2","q":"A2","recapture":"A2"},"B2":{"p":"B2","q":"B2","recapture":"B2"}},
                "unsafe_probe":"u","unsafe_transitions":{"A0":"AU","B0":"BU"},"allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]}
    if label=="unidentified_initial_converges_to_safe_terminal":
        return {"name":label,"initial":["C0","D0"],"outputs":{"C0":"READY","D0":"READY","Z":"READY"},
                "effect_envelopes":{"C0":"OLD_C_ONLY","D0":"OLD_D_ONLY","Z":"CURRENT_TARGET_ALLOWED"},
                "transitions":{"C0":{"p":"Z","q":"C0","recapture":"C0"},"D0":{"p":"Z","q":"D0","recapture":"D0"},
                               "Z":{"p":"Z","q":"Z","recapture":"Z"}},"allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]}
    if label=="initial_action_equivalent_without_identity":
        return {"name":label,"initial":["I0","J0"],"outputs":{"I0":"READY","J0":"READY"},
                "effect_envelopes":{"I0":"CURRENT_TARGET_ALLOWED","J0":"CURRENT_TARGET_ALLOWED"},
                "transitions":{"I0":{"p":"I0","q":"I0","recapture":"I0"},"J0":{"p":"J0","q":"J0","recapture":"J0"}},
                "allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]}
    if label=="action_different_safe_bisimulation":
        names=("E0","F0","E1","F1","EU","FU")
        obs={s:"READY" for s in names}; obs.update(EU="LEFT",FU="RIGHT")
        return {"name":label,"initial":["E0","F0"],"outputs":obs,
                "effect_envelopes":{"E0":"EFFECT_E","F0":"EFFECT_F","E1":"EFFECT_E","F1":"EFFECT_F"},
                "transitions":{"E0":{"p":"E1","q":"E1","recapture":"E0"},"F0":{"p":"F1","q":"F1","recapture":"F0"},
                               "E1":{"p":"E1","q":"E1","recapture":"E1"},"F1":{"p":"F1","q":"F1","recapture":"F1"}},
                "unsafe_probe":"u","unsafe_transitions":{"E0":"EU","F0":"FU"},
                "bisimulation_relation":[["E0","F0"],["E1","F1"]],"allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]}
    raise AssertionError(label)


def expected_leaf(states,m):
    envelopes=sorted({m["effect_envelopes"][s] for s in states})
    if len(states)==1: kind="CURRENT_TERMINAL_SINGLETON"
    elif len(envelopes)==1: kind="ACTION_EQUIVALENT_CURRENT"
    else: kind="AMBIGUOUS_CURRENT"
    allowed=set(envelopes)<=set(m["allowed_effect_envelopes"])
    return {"kind":"leaf","terminal_states":sorted(states),"terminal_effect_envelopes":envelopes,
            "epistemic_status":kind,"initial_identity_claim":False,
            "terminal_decision":"ALLOW_SCOPED_EFFECT" if allowed else "YIELD_OR_REOBSERVE"}


def enumerate_independently(states,depth,m):
    leaf=expected_leaf(states,m)
    if leaf["epistemic_status"]!="AMBIGUOUS_CURRENT" or depth==0: return [leaf]
    out=[leaf]
    for act in PERMITTED:
        classes={}
        for state in states:
            target=m["transitions"][state][act]
            classes.setdefault(m["outputs"][target],set()).add(target)
        symbols=sorted(classes)
        combinations=[{}]
        for symbol in symbols:
            children=enumerate_independently(frozenset(classes[symbol]),depth-1,m)
            combinations=[dict(prev,**{symbol:child}) for prev in combinations for child in children]
        out.extend({"kind":"probe","probe":act,"belief":sorted(states),"branches":tree} for tree in combinations)
    return out


def tree_belief(tree):
    if tree["kind"]=="leaf": return set(tree["terminal_states"])
    return set(tree["belief"])


def validate(tree,belief,m,depth):
    if tree.get("kind")=="leaf": return tree==expected_leaf(belief,m)
    action=tree.get("probe")
    if action not in PERMITTED or depth<1 or tree.get("belief")!=sorted(belief): return False
    partition={}
    for state in belief:
        target=m["transitions"][state][action]
        partition.setdefault(m["outputs"][target],set()).add(target)
    branches=tree.get("branches")
    if not isinstance(branches,dict) or set(branches)!=set(partition): return False
    return all(validate(branches[symbol],frozenset(partition[symbol]),m,depth-1) for symbol in partition)


def decision_rows(tree,depth=0,cost=0):
    if tree["kind"]=="leaf":
        return [{"depth":depth,"cost":cost,"states":tree["terminal_states"],"effects":tree["terminal_effect_envelopes"],
                 "epistemic":tree["epistemic_status"],"decision":tree["terminal_decision"],"initial_identity_claim":False}]
    return [row for child in tree["branches"].values() for row in decision_rows(child,depth+1,cost+WEIGHTS[tree["probe"]])]


def closed(rel,m):
    pairs={tuple(pair) for pair in rel}
    return all(m["outputs"][a]==m["outputs"][b] and all((m["transitions"][a][x],m["transitions"][b][x]) in pairs for x in PERMITTED) for a,b in pairs)


def trace(s,word,m):
    result=[m["outputs"][s]]
    for act in word:
        s=m["transitions"][s][act]; result.append(m["outputs"][s])
    return tuple(result)


def main():
    raw_path=Path(sys.argv[1]); data=raw_path.read_bytes(); raw=json.loads(data)
    assert data.endswith(b"\n") and canon(raw).encode()+b"\n"==data
    assert raw["allocation_id"]==ALLOCATION
    models=[oracle(n) for n in ("separates_initial_but_stales_terminal_action","unidentified_initial_converges_to_safe_terminal",
                                "initial_action_equivalent_without_identity","action_different_safe_bisimulation")]
    specification={"safe_probes":list(PERMITTED),"cost":WEIGHTS,"max_depth":MAX,"cases":models}
    assert raw["spec"]==specification and raw["spec_sha256"]==hashlib.sha256(canon(specification).encode()).hexdigest()
    by_name={row["case"]:row["layers"] for row in raw["results"]}
    assert set(by_name)=={m["name"] for m in models}
    for model in models:
        layers=by_name[model["name"]]; assert len(layers)==MAX+1
        for k,layer in enumerate(layers):
            expected=enumerate_independently(frozenset(model["initial"]),k,model)
            assert layer["depth_limit"]==k and layer["tree_count"]==len(expected)
            assert sorted(map(canon,expected))==sorted(map(canon,layer["trees"]))
            assert hashlib.sha256("\n".join(sorted(map(canon,expected))).encode()).hexdigest()==layer["trees_sha256_sorted"]
            solvable=[t for t in expected if "AMBIGUOUS_CURRENT" not in flatten(t)]
            optimum=min(solvable,key=lambda t:(max(x["depth"] for x in decision_rows(t)),max(x["cost"] for x in decision_rows(t)),sum(x["depth"] for x in decision_rows(t)),canon(t))) if solvable else None
            assert canon(layer["selected"])==canon(optimum)
            assert layer["selected_terminal_rows"]==([] if optimum is None else decision_rows(optimum))
        words=[w for n in range(MAX+1) for w in itertools.product(PERMITTED,repeat=n)]
        distinguish=[w for w in words if trace(model["initial"][0],w,model)!=trace(model["initial"][1],w,model)]
        if model["name"]=="separates_initial_but_stales_terminal_action":
            assert layers[0]["selected"] is None and layers[1]["selected"] is None
            selected=layers[2]["selected"]
            assert min(map(len,distinguish))==2 and selected is not None
            assert all(row["decision"]=="YIELD_OR_REOBSERVE" for row in layers[2]["selected_terminal_rows"])
            assert all(row["effects"] in (["STALE_TARGET_A_FORBIDDEN"],["STALE_TARGET_B_FORBIDDEN"]) for row in layers[2]["selected_terminal_rows"])
        elif model["name"]=="unidentified_initial_converges_to_safe_terminal":
            selected=layers[1]["selected"]
            assert selected is not None and selected["probe"]=="p"
            rows=layers[1]["selected_terminal_rows"]
            assert len(rows)==1 and rows[0]["states"]==["Z"] and rows[0]["decision"]=="ALLOW_SCOPED_EFFECT"
            assert not rows[0]["initial_identity_claim"] and not distinguish
        elif model["name"]=="initial_action_equivalent_without_identity":
            selected=layers[0]["selected"]
            assert selected is not None and selected["kind"]=="leaf"
            assert selected["epistemic_status"]=="ACTION_EQUIVALENT_CURRENT" and not selected["initial_identity_claim"]
        else:
            assert layers[2]["selected"] is None and not distinguish
            assert closed(model["bisimulation_relation"],model)
            unsafe={model["unsafe_transitions"][s]:model["outputs"][model["unsafe_transitions"][s]] for s in model["initial"]}
            assert len(set(unsafe.values()))==2
    # Frozen mutation controls, each applied to the actual structural validator.
    stale=by_name["separates_initial_but_stales_terminal_action"][2]["selected"]
    assert stale is not None
    unsafe=json.loads(json.dumps(stale)); unsafe["probe"]="u"
    assert not validate(unsafe,frozenset(models[0]["initial"]),models[0],MAX)
    dropped=json.loads(json.dumps(stale)); dropped["branches"].pop(next(iter(dropped["branches"])))
    assert not validate(dropped,frozenset(models[0]["initial"]),models[0],MAX)
    singleton={"kind":"leaf","terminal_states":["A0"],"terminal_effect_envelopes":["OLD_TARGET_ALLOWED_A"],
               "epistemic_status":"CURRENT_TERMINAL_SINGLETON","initial_identity_claim":False,"terminal_decision":"YIELD_OR_REOBSERVE"}
    assert not validate(singleton,frozenset(models[0]["initial"]),models[0],MAX)
    def replace_leaves(node,fn):
        if node["kind"]=="leaf": return fn(json.loads(json.dumps(node)))
        node["branches"]={k:replace_leaves(v,fn) for k,v in node["branches"].items()}; return node
    stale_action=replace_leaves(json.loads(json.dumps(stale)),lambda x:{**x,"terminal_decision":"ALLOW_SCOPED_EFFECT"})
    assert not validate(stale_action,frozenset(models[0]["initial"]),models[0],MAX)
    conv=by_name["unidentified_initial_converges_to_safe_terminal"][1]["selected"]
    false_conv=replace_leaves(json.loads(json.dumps(conv)),lambda x:{**x,"terminal_effect_envelopes":["OLD_C_ONLY"],"terminal_decision":"ALLOW_SCOPED_EFFECT"})
    assert not validate(false_conv,frozenset(models[1]["initial"]),models[1],1)
    assert not closed([["E0","F0"]],models[3])
    recapture={"kind":"probe","probe":"recapture","belief":models[0]["initial"],"branches":{"READY":singleton}}
    assert not validate(recapture,frozenset(models[0]["initial"]),models[0],MAX)
    print(json.dumps({"allocation_id":ALLOCATION,"raw_sha256":hashlib.sha256(data).hexdigest(),
                      "fixture_pairs":4,"tree_layers":12,"mutation_rejections":7,"disposition":"PASS_METHOD_SCOPED"},sort_keys=True))


def flatten(tree):
    if tree["kind"]=="leaf": return [tree["epistemic_status"]]
    return [x for child in tree["branches"].values() for x in flatten(child)]


if __name__=="__main__": main()

#!/usr/bin/env python3
"""Independent raw-only verifier for #6147 A05; no candidate imports."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

IDENT="AI-6147-T0-20261003-05"
ALPHABET=("p","q","recapture")
LIMIT=2
UNIT={x:1 for x in ALPHABET}

def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)

def reference_machine():
    nodes=("C0","D0","C1","D1","Z","CU","DU")
    observed={x:"READY" for x in nodes}; observed.update(CU="LEFT",DU="RIGHT")
    return {"initial":["C0","D0"],"outputs":observed,
            "effect_envelopes":{"C0":"INITIAL_C_ONLY","D0":"INITIAL_D_ONLY","C1":"INTERMEDIATE_C_ONLY","D1":"INTERMEDIATE_D_ONLY","Z":"CURRENT_TARGET_ALLOWED"},
            "transitions":{"C0":{"p":"C1","q":"C0","recapture":"C0"},"D0":{"p":"D1","q":"D0","recapture":"D0"},
                           "C1":{"p":"C1","q":"Z","recapture":"C1"},"D1":{"p":"D1","q":"Z","recapture":"D1"},
                           "Z":{"p":"Z","q":"Z","recapture":"Z"}},
            "unsafe_probe":"u","unsafe_transitions":{"C0":"CU","D0":"DU"},
            "allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]}

def terminal(states,m):
    effects=sorted({m["effect_envelopes"][s] for s in states})
    epistemic="CURRENT_TERMINAL_SINGLETON" if len(states)==1 else ("ACTION_EQUIVALENT_CURRENT" if len(effects)==1 else "AMBIGUOUS_CURRENT")
    action="ALLOW_SCOPED_EFFECT" if set(effects)<=set(m["allowed_effect_envelopes"]) else "YIELD_OR_REOBSERVE"
    return {"kind":"leaf","terminal_states":sorted(states),"terminal_effect_envelopes":effects,
            "epistemic_status":epistemic,"initial_identity_claim":False,"terminal_decision":action}

def oracle_trees(states,remaining,m):
    end=terminal(states,m)
    if end["epistemic_status"]!="AMBIGUOUS_CURRENT" or remaining==0: return [end]
    answer=[end]
    for move in ALPHABET:
        next_belief={}
        for state in states:
            successor=m["transitions"][state][move]
            next_belief.setdefault(m["outputs"][successor],set()).add(successor)
        symbols=sorted(next_belief)
        partial=[{}]
        for symbol in symbols:
            choices=oracle_trees(frozenset(next_belief[symbol]),remaining-1,m)
            partial=[{**prefix,symbol:choice} for prefix in partial for choice in choices]
        answer += [{"kind":"probe","probe":move,"belief":sorted(states),"branches":p} for p in partial]
    return answer

def check_policy(policy,belief,m,remaining):
    if policy.get("kind")=="leaf": return policy==terminal(belief,m)
    if set(policy)!={"kind","probe","belief","branches"}: return False
    action=policy.get("probe")
    if action not in ALPHABET or remaining<1 or policy.get("belief")!=sorted(belief): return False
    dests={}
    for state in belief:
        nxt=m["transitions"][state][action]
        dests.setdefault(m["outputs"][nxt],set()).add(nxt)
    if set(policy.get("branches",{}))!=set(dests): return False
    return all(check_policy(policy["branches"][o],frozenset(dests[o]),m,remaining-1) for o in dests)

def route(tree,depth=0,cost=0):
    if tree["kind"]=="leaf":
        return [{"depth":depth,"cost":cost,"states":tree["terminal_states"],"effects":tree["terminal_effect_envelopes"],
                 "status":tree["epistemic_status"],"decision":tree["terminal_decision"],"initial_identity_claim":False}]
    return [r for child in tree["branches"].values() for r in route(child,depth+1,cost+UNIT[tree["probe"]])]

def statuses(tree):
    if tree["kind"]=="leaf": return [tree["epistemic_status"]]
    return [s for child in tree["branches"].values() for s in statuses(child)]

def observed_trace(state,word,m):
    obs=[m["outputs"][state]]
    for action in word:
        state=m["transitions"][state][action]; obs.append(m["outputs"][state])
    return tuple(obs)

def main():
    file=Path(sys.argv[1]); data=file.read_bytes(); raw=json.loads(data)
    assert data.endswith(b"\n") and canonical(raw).encode()+b"\n"==data
    assert raw["allocation_id"]==IDENT
    m=reference_machine(); spec={"safe_probes":list(ALPHABET),"cost":UNIT,"max_depth":LIMIT,"machine":m}
    assert raw["spec"]==spec and raw["spec_sha256"]==hashlib.sha256(canonical(spec).encode()).hexdigest()
    layers=raw["layers"]; assert len(layers)==LIMIT+1
    for depth,layer in enumerate(layers):
        all_expected=oracle_trees(frozenset(m["initial"]),depth,m)
        assert layer["depth_limit"]==depth and layer["tree_count"]==len(all_expected)
        assert sorted(map(canonical,layer["trees"]))==sorted(map(canonical,all_expected))
        assert layer["trees_sha256_sorted"]==hashlib.sha256("\n".join(sorted(map(canonical,all_expected))).encode()).hexdigest()
        complete=[t for t in all_expected if "AMBIGUOUS_CURRENT" not in statuses(t)]
        best=min(complete,key=lambda t:(max(r["depth"] for r in route(t)),max(r["cost"] for r in route(t)),sum(r["depth"] for r in route(t)),canonical(t))) if complete else None
        assert canonical(layer["selected"])==canonical(best)
        assert layer["selected_terminal_rows"]==([] if best is None else route(best))
    all_words=[w for n in range(LIMIT+1) for w in itertools.product(ALPHABET,repeat=n)]
    assert all(observed_trace("C0",w,m)==observed_trace("D0",w,m) for w in all_words)
    selected=layers[2]["selected"]
    assert selected is not None and selected["probe"]=="p"
    child=selected["branches"]["READY"]
    assert child["kind"]=="probe" and child["probe"]=="q"
    terminal_rows=layers[2]["selected_terminal_rows"]
    assert terminal_rows==[{"depth":2,"cost":2,"states":["Z"],"effects":["CURRENT_TARGET_ALLOWED"],
                           "status":"CURRENT_TERMINAL_SINGLETON","decision":"ALLOW_SCOPED_EFFECT","initial_identity_claim":False}]
    # The unsafe one-step action is observably informative, but not admissible.
    unsafe_outputs={m["outputs"][m["unsafe_transitions"][s]] for s in m["initial"]}
    assert unsafe_outputs=={"LEFT","RIGHT"}
    # Directly exercise each negative mutation with the structural validator.
    bad=json.loads(json.dumps(selected)); bad["probe"]="u"
    assert not check_policy(bad,frozenset(m["initial"]),m,LIMIT)
    missing=json.loads(json.dumps(selected)); missing["branches"].pop("READY")
    assert not check_policy(missing,frozenset(m["initial"]),m,LIMIT)
    leaked=json.loads(json.dumps(selected)); leaked["initial_identity_claim"]=True
    assert not check_policy(leaked,frozenset(m["initial"]),m,LIMIT)
    def mutate_leaves(node,fn):
        if node["kind"]=="leaf": return fn(json.loads(json.dumps(node)))
        node["branches"]={k:mutate_leaves(v,fn) for k,v in node["branches"].items()}; return node
    stale=mutate_leaves(json.loads(json.dumps(selected)),lambda x:{**x,"terminal_effect_envelopes":["INITIAL_C_ONLY"],"terminal_decision":"ALLOW_SCOPED_EFFECT"})
    assert not check_policy(stale,frozenset(m["initial"]),m,LIMIT)
    false_merge=mutate_leaves(json.loads(json.dumps(selected)),lambda x:{**x,"terminal_states":["C1","D1"],"terminal_effect_envelopes":["CURRENT_TARGET_ALLOWED"]})
    assert not check_policy(false_merge,frozenset(m["initial"]),m,LIMIT)
    recapture={"kind":"probe","probe":"recapture","belief":m["initial"],"branches":{"READY":{"kind":"leaf","terminal_states":["C0"],
               "terminal_effect_envelopes":["INITIAL_C_ONLY"],"epistemic_status":"CURRENT_TERMINAL_SINGLETON","initial_identity_claim":True,"terminal_decision":"ALLOW_SCOPED_EFFECT"}}}
    assert not check_policy(recapture,frozenset(m["initial"]),m,LIMIT)
    print(json.dumps({"allocation_id":IDENT,"raw_sha256":hashlib.sha256(data).hexdigest(),"policy_layers":3,
                      "safe_words_checked":len(all_words),"mutation_rejections":6,"disposition":"PASS_METHOD_SCOPED"},sort_keys=True))

if __name__=="__main__": main()

#!/usr/bin/env python3
"""Independent raw-only verifier; does not import candidate.py."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

ALLOCATION = "AI-6147-T0-20261003-03"
ALPHABET = ("p", "q", "recapture")
MAX_DEPTH = 2
PRICE = {"p": 1, "q": 1, "recapture": 1}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def oracle(name):
    if name == "separable_action_different":
        states = ("A0", "B0", "A1", "B1", "AQ", "BQ", "AL", "BR")
        obs = {s: "READY" for s in states}; obs["AL"] = "LEFT"; obs["BR"] = "RIGHT"
        move = {"A0": {"p":"A1","q":"AQ","recapture":"A0"}, "B0": {"p":"B1","q":"BQ","recapture":"B0"},
                "A1": {"p":"A1","q":"AL","recapture":"A1"}, "B1": {"p":"B1","q":"BR","recapture":"B1"},
                "AQ": {"p":"AQ","q":"AQ","recapture":"AQ"}, "BQ": {"p":"BQ","q":"BQ","recapture":"BQ"},
                "AL": {"p":"AL","q":"AL","recapture":"AL"}, "BR": {"p":"BR","q":"BR","recapture":"BR"}}
        return {"name":name,"initial":["A0","B0"],"outputs":obs,
                "effect_envelopes":{s:("SUBMIT_ALLOWED" if s.startswith("A") else "SUBMIT_FORBIDDEN") for s in states},
                "transitions":move,"unsafe_probe":"u","unsafe_successors":{"A0":"AL","B0":"BR"}}
    if name == "action_equivalent_alias":
        states=("C0","D0","C1","D1")
        return {"name":name,"initial":["C0","D0"],"outputs":{s:"READY" for s in states},
                "effect_envelopes":{s:"SAME_SAFE_EFFECT" for s in states},
                "transitions":{"C0":{"p":"C1","q":"C1","recapture":"C0"},"D0":{"p":"D1","q":"D1","recapture":"D0"},
                               "C1":{"p":"C1","q":"C1","recapture":"C1"},"D1":{"p":"D1","q":"D1","recapture":"D1"}}}
    if name == "safe_bisimulation_impossible":
        states=("E0","F0","E1","F1","EL","FR")
        obs={s:"READY" for s in states}; obs["EL"]="LEFT"; obs["FR"]="RIGHT"
        return {"name":name,"initial":["E0","F0"],"outputs":obs,
                "effect_envelopes":{s:("EFFECT_E" if s.startswith("E") else "EFFECT_F") for s in states},
                "transitions":{"E0":{"p":"E1","q":"E1","recapture":"E0"},"F0":{"p":"F1","q":"F1","recapture":"F0"},
                               "E1":{"p":"E1","q":"E1","recapture":"E1"},"F1":{"p":"F1","q":"F1","recapture":"F1"},
                               "EL":{"p":"EL","q":"EL","recapture":"EL"},"FR":{"p":"FR","q":"FR","recapture":"FR"}},
                "unsafe_probe":"u","unsafe_successors":{"E0":"EL","F0":"FR"},
                "bisimulation_relation":[["E0","F0"],["E1","F1"]]}
    raise ValueError(name)


def tree_space(belief, remaining, machine):
    effects={machine["effect_envelopes"][s] for s in belief}
    disposition="IDENTIFIED" if len(belief)==1 else ("ACTION_EQUIVALENT" if len(effects)==1 else None)
    if disposition:
        return [{"kind":"leaf","belief":sorted(belief),"disposition":disposition,"reachable_effect_envelopes":sorted(effects)}]
    leaf={"kind":"leaf","belief":sorted(belief),"disposition":"YIELD","reachable_effect_envelopes":sorted(effects)}
    policies=[leaf]
    if remaining == 0: return policies
    for action in ALPHABET:
        outcomes={}
        for state in belief:
            successor=machine["transitions"][state][action]
            outcomes.setdefault(machine["outputs"][successor],set()).add(successor)
        labels=sorted(outcomes)
        product=[{}]
        for symbol in labels:
            children=tree_space(frozenset(outcomes[symbol]),remaining-1,machine)
            product=[dict(prefix,**{symbol:child}) for prefix in product for child in children]
        policies.extend({"kind":"probe","probe":action,"belief":sorted(belief),"branches":p} for p in product)
    return policies


def paths(tree, depth=0, cost=0):
    if tree["kind"]=="leaf": return [(depth,cost)]
    result=[]
    for child in tree["branches"].values(): result.extend(paths(child,depth+1,cost+PRICE[tree["probe"]]))
    return result


def outcome_word(state, word, machine):
    trace=[machine["outputs"][state]]
    for action in word:
        state=machine["transitions"][state][action]
        trace.append(machine["outputs"][state])
    return tuple(trace)


def relation_is_closed(relation,machine):
    pairs={tuple(pair) for pair in relation}
    return all(machine["outputs"][a]==machine["outputs"][b] and
               all((machine["transitions"][a][x],machine["transitions"][b][x]) in pairs for x in ALPHABET)
               for a,b in pairs)


def main():
    raw_file=Path(sys.argv[1]); data=raw_file.read_bytes(); raw=json.loads(data)
    assert data.endswith(b"\n") and canonical(raw).encode()+b"\n"==data
    assert raw["allocation_id"]==ALLOCATION
    machines=[oracle(n) for n in ("separable_action_different","action_equivalent_alias","safe_bisimulation_impossible")]
    fixture={"safe_probes":list(ALPHABET),"cost":PRICE,"max_depth":MAX_DEPTH,"cases":machines}
    assert raw["fixture"]==fixture
    assert raw["fixture_sha256"]==hashlib.sha256(canonical(fixture).encode()).hexdigest()
    by_name={x["case"]:x["layers"] for x in raw["result"]}
    assert set(by_name)=={m["name"] for m in machines}
    for machine in machines:
        layers=by_name[machine["name"]]
        assert len(layers)==MAX_DEPTH+1
        for depth,layer in enumerate(layers):
            assert layer["depth_limit"]==depth
            expected=tree_space(frozenset(machine["initial"]),depth,machine)
            assert sorted(map(canonical,expected))==sorted(map(canonical,layer["policy_trees"]))
            assert len(expected)==layer["policy_tree_count"]
            assert hashlib.sha256("\n".join(sorted(map(canonical,expected))).encode()).hexdigest()==layer["policy_tree_sha256_sorted"]
            complete=[t for t in expected if all(d!="YIELD" for d in leaf_status(t))]
            assert len(complete)==layer["resolved_policy_trees"]
            selected=layer["selected_policy"]
            expected_selected=min(complete,key=lambda t:(max(v[0] for v in paths(t)),max(v[1] for v in paths(t)),sum(v[0] for v in paths(t)),canonical(t))) if complete else None
            assert canonical(selected)==canonical(expected_selected)
            if selected:
                assert terminal_envelopes_match(selected,machine)
                assert "u" not in canonical(selected)
        words=[w for n in range(MAX_DEPTH+1) for w in itertools.product(ALPHABET,repeat=n)]
        separated=[w for w in words if outcome_word(machine["initial"][0],w,machine)!=outcome_word(machine["initial"][1],w,machine)]
        if machine["name"]=="separable_action_different":
            assert layers[0]["selected_policy"] is None and layers[1]["selected_policy"] is None
            assert min(map(len,separated))==2
            assert outcome_word("A0",("p","q"),machine)!=outcome_word("B0",("p","q"),machine)
        elif machine["name"]=="action_equivalent_alias":
            assert layers[0]["selected_policy"]["disposition"]=="ACTION_EQUIVALENT" and not separated
        else:
            assert layers[2]["selected_policy"] is None and not separated
            assert relation_is_closed(machine["bisimulation_relation"],machine)
    # Mutation gates: deliberately malformed policies/relations must not verify.
    sep=by_name["separable_action_different"][2]["selected_policy"]
    assert sep is not None and sep["kind"]=="probe"
    assert sep["probe"] in ALPHABET and "u" not in ALPHABET
    omitted=json.loads(json.dumps(sep)); omitted["branches"].pop(next(iter(omitted["branches"])))
    assert not valid_policy_shape(omitted,tuple(machines[0]["initial"]),machines[0],2)
    fake={"kind":"leaf","belief":machines[0]["initial"],"disposition":"IDENTIFIED","reachable_effect_envelopes":["SUBMIT_ALLOWED","SUBMIT_FORBIDDEN"]}
    assert not valid_policy_shape(fake,tuple(machines[0]["initial"]),machines[0],2)
    assert not relation_is_closed([["E0","F0"]],machines[2])
    recapture={"kind":"probe","probe":"recapture","belief":machines[0]["initial"],"branches":{"READY":fake}}
    assert not valid_policy_shape(recapture,tuple(machines[0]["initial"]),machines[0],2)
    print(json.dumps({"allocation_id":ALLOCATION,"disposition":"PASS_METHOD_SCOPED","raw_sha256":hashlib.sha256(data).hexdigest(),
                      "cases":3,"depth_layers":9,"mutation_controls_rejected":5},sort_keys=True))


def leaf_status(tree):
    if tree["kind"]=="leaf": return [tree["disposition"]]
    return [x for child in tree["branches"].values() for x in leaf_status(child)]


def flatten_envelopes(tree):
    if tree["kind"]=="leaf": return tree["reachable_effect_envelopes"]
    return [x for child in tree["branches"].values() for x in flatten_envelopes(child)]


def flatten_envelopes_for_beliefs(tree,machine):
    if tree["kind"]=="leaf": return sorted({machine["effect_envelopes"][s] for s in tree["belief"]})
    return [x for child in tree["branches"].values() for x in flatten_envelopes_for_beliefs(child,machine)]


def terminal_envelopes_match(tree,machine):
    if tree["kind"]=="leaf":
        expected=sorted({machine["effect_envelopes"][s] for s in tree["belief"]})
        return tree.get("reachable_effect_envelopes")==expected
    return all(terminal_envelopes_match(child,machine) for child in tree["branches"].values())


def valid_policy_shape(tree,belief,machine,depth):
    if tree.get("kind")=="leaf":
        env={machine["effect_envelopes"][s] for s in belief}
        return tree.get("belief")==sorted(belief) and tree.get("disposition")==("IDENTIFIED" if len(belief)==1 else ("ACTION_EQUIVALENT" if len(env)==1 else "YIELD"))
    if depth<=0 or tree.get("probe") not in ALPHABET or tree.get("belief")!=sorted(belief): return False
    groups={}
    for state in belief:
        nxt=machine["transitions"][state][tree["probe"]]
        groups.setdefault(machine["outputs"][nxt],set()).add(nxt)
    return set(tree.get("branches",{}))==set(groups) and all(valid_policy_shape(tree["branches"][o],tuple(sorted(states)),machine,depth-1) for o,states in groups.items())


if __name__=="__main__": main()

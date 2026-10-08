#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #6147 T0; does not import candidate.py."""
import hashlib
import json
import sys
from pathlib import Path

ALLOCATION = "AI-6147-T0-20261002-02"
SAFE = ("p", "q", "recapture")
COST = {"p": 1, "q": 1, "recapture": 1}
DEPTH = 2


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def oracle_case(name):
    if name == "separable_action_different":
        outputs = {"A0":"READY","B0":"READY","A1":"READY","B1":"READY","AQ":"READY","BQ":"READY","AQ1":"READY","BQ1":"READY","AL":"LEFT","BR":"RIGHT"}
        envelope = {s:("SUBMIT_ALLOWED" if s[0]=="A" else "SUBMIT_FORBIDDEN") for s in outputs}
        delta = {"A0":{"p":"A1","q":"AQ","recapture":"A0"},"B0":{"p":"B1","q":"BQ","recapture":"B0"},"A1":{"p":"A1","q":"AL","recapture":"A1"},"B1":{"p":"B1","q":"BR","recapture":"B1"},"AQ":{"p":"AQ1","q":"AQ1","recapture":"AQ"},"BQ":{"p":"BQ1","q":"BQ1","recapture":"BQ"},"AQ1":{"p":"AQ1","q":"AQ1","recapture":"AQ1"},"BQ1":{"p":"BQ1","q":"BQ1","recapture":"BQ1"},"AL":{"p":"AL","q":"AL","recapture":"AL"},"BR":{"p":"BR","q":"BR","recapture":"BR"}}
        return {"name":name,"initial":["A0","B0"],"outputs":outputs,"effect_envelopes":envelope,"transitions":delta,"unsafe_probe":"u","unsafe_successors":{"A0":"AL","B0":"BR"}}
    if name == "action_equivalent_alias":
        outputs={"C0":"READY","D0":"READY","C1":"READY","D1":"READY"}
        delta={"C0":{"p":"C1","q":"C1","recapture":"C0"},"D0":{"p":"D1","q":"D1","recapture":"D0"},"C1":{"p":"C1","q":"C1","recapture":"C1"},"D1":{"p":"D1","q":"D1","recapture":"D1"}}
        return {"name":name,"initial":["C0","D0"],"outputs":outputs,"effect_envelopes":{s:"SAME_SAFE_EFFECT" for s in outputs},"transitions":delta}
    if name == "safe_bisimulation_impossible":
        outputs={"E0":"READY","F0":"READY","E1":"READY","F1":"READY","EL":"LEFT","FR":"RIGHT"}
        delta={"E0":{"p":"E1","q":"E1","recapture":"E0"},"F0":{"p":"F1","q":"F1","recapture":"F0"},"E1":{"p":"E1","q":"E1","recapture":"E1"},"F1":{"p":"F1","q":"F1","recapture":"F1"},"EL":{"p":"EL","q":"EL","recapture":"EL"},"FR":{"p":"FR","q":"FR","recapture":"FR"}}
        return {"name":name,"initial":["E0","F0"],"outputs":outputs,"effect_envelopes":{s:("EFFECT_E" if s[0]=="E" else "EFFECT_F") for s in outputs},"transitions":delta,"unsafe_probe":"u","unsafe_successors":{"E0":"EL","F0":"FR"},"bisimulation_relation":[["E0","F0"],["E1","F1"]]}
    raise AssertionError("unexpected case")


def all_words(k):
    words=[()]
    for n in range(1,k+1):
        def rec(prefix,left):
            if left==0:
                words.append(prefix);return
            for a in SAFE: rec(prefix+(a,),left-1)
        rec((),n)
    return words


def signature(state, word, case):
    trace=[case["outputs"][state]]
    for action in word:
        state=case["transitions"][state][action]
        trace.append(case["outputs"][state])
    return tuple(trace)


def verify_policy(tree, belief, case, depth_left):
    if tree["kind"]=="leaf":
        if sorted(belief)!=tree.get("belief"): return False
        envelopes={case["effect_envelopes"][s] for s in belief}
        if tree.get("disposition")=="IDENTIFIED": return len(belief)==1
        if tree.get("disposition")=="ACTION_EQUIVALENT": return len(envelopes)==1
        return tree.get("disposition")=="YIELD" and len(envelopes)>1 and depth_left>=0
    if depth_left<=0 or tree.get("probe") not in SAFE or sorted(belief)!=tree.get("belief"): return False
    groups={}
    for state in belief:
        nxt=case["transitions"][state][tree["probe"]]
        groups.setdefault(case["outputs"][nxt],[]).append(nxt)
    branches=tree.get("branches",{})
    if set(branches)!=set(groups): return False
    return all(verify_policy(branches[o],groups[o],case,depth_left-1) for o in groups)


def relation_closed(relation, case):
    pairs={tuple(x) for x in relation}
    for left,right in pairs:
        if case["outputs"].get(left)!=case["outputs"].get(right): return False
        for action in SAFE:
            if (case["transitions"][left][action],case["transitions"][right][action]) not in pairs: return False
    return True


def terminal_list(tree):
    if tree["kind"]=="leaf": return [tree["disposition"]]
    return [d for child in tree["branches"].values() for d in terminal_list(child)]


def independent_tree_space(belief, depth, case):
    """Enumerate policies independently using immutable frozenset beliefs."""
    envelope_ids={case["effect_envelopes"][s] for s in belief}
    leaf_type="IDENTIFIED" if len(belief)==1 else ("ACTION_EQUIVALENT" if len(envelope_ids)==1 else None)
    if leaf_type:
        return [{"kind":"leaf","belief":sorted(belief),"disposition":leaf_type}]
    policies=[{"kind":"leaf","belief":sorted(belief),"disposition":"YIELD"}]
    if depth<1:
        return policies
    for probe in SAFE:
        destinations={}
        for state in belief:
            nxt=case["transitions"][state][probe]
            destinations.setdefault(case["outputs"][nxt],set()).add(nxt)
        partial=[{}]
        for observed in sorted(destinations):
            child_options=independent_tree_space(frozenset(destinations[observed]),depth-1,case)
            partial=[{**prefix,observed:child} for prefix in partial for child in child_options]
        policies.extend({"kind":"probe","probe":probe,"belief":sorted(belief),"branches":branches} for branches in partial)
    return policies


def tree_costs(tree):
    if tree["kind"]=="leaf": return [(0,0)]
    rows=[]
    for child in tree["branches"].values():
        rows.extend((depth+1,cost+COST[tree["probe"]]) for depth,cost in tree_costs(child))
    return rows


def main():
    raw_path=Path(sys.argv[1]); raw_bytes=raw_path.read_bytes(); raw=json.loads(raw_bytes)
    assert raw_bytes.endswith(b"\n") and canon(raw).encode()+b"\n"==raw_bytes
    assert raw["allocation_id"]==ALLOCATION
    cases=[oracle_case(n) for n in ("separable_action_different","action_equivalent_alias","safe_bisimulation_impossible")]
    fixture={"safe_probes":list(SAFE),"cost":COST,"max_depth":DEPTH,"cases":cases}
    assert raw["fixture"]==fixture
    assert raw["fixture_sha256"]==hashlib.sha256(canon(fixture).encode()).hexdigest()
    results={r["case"]:r for r in raw["result"]}
    assert set(results)=={c["name"] for c in cases}
    checks=[]
    for case in cases:
        layers=results[case["name"]]["layers"]
        assert [x["depth_limit"] for x in layers]==[0,1,2]
        for layer in layers:
            trees=layer["policy_trees"]
            expected=independent_tree_space(frozenset(case["initial"]),layer["depth_limit"],case)
            assert len(trees)==layer["policy_tree_count"]
            assert sorted(map(canon,trees))==sorted(map(canon,expected))
            assert hashlib.sha256("\n".join(sorted(map(canon,trees))).encode()).hexdigest()==layer["policy_tree_sha256_sorted"]
            assert sum(all(d in ("IDENTIFIED","ACTION_EQUIVALENT") for d in terminal_list(t)) for t in trees)==layer["resolved_policy_trees"]
            for t in trees: assert verify_policy(t,tuple(case["initial"]),case,layer["depth_limit"])
            selected=layer["selected_policy"]
            if selected is not None:
                assert verify_policy(selected,tuple(case["initial"]),case,layer["depth_limit"])
                resolved=[t for t in trees if all(d in ("IDENTIFIED","ACTION_EQUIVALENT") for d in terminal_list(t))]
                def rank(t):
                    cm=tree_costs(t)
                    return (max((x[0] for x in cm),default=0),max((x[1] for x in cm),default=0),sum(x[0] for x in cm),canon(t))
                assert canon(selected)==canon(min(resolved,key=rank))
                assert "u" not in json.dumps(selected)
        # Independent exact search over fixed words is complete for a two-hypothesis deterministic pair:
        # until outputs diverge both states take the same observable branch, so adaptation adds no separating power.
        words=all_words(DEPTH)
        separating=[]
        for w in words:
            if signature(case["initial"][0],w,case)!=signature(case["initial"][1],w,case): separating.append(w)
        if case["name"]=="separable_action_different":
            assert layers[0]["selected_policy"] is None and layers[1]["selected_policy"] is None
            chosen=layers[2]["selected_policy"]
            assert chosen is not None and verify_policy(chosen,tuple(case["initial"]),case,2)
            assert min(map(len,separating))==2
            assert signature("A0",("p","q"),case)!=signature("B0",("p","q"),case)
            checks.append("separable_pair_minimum_safe_depth_2")
        elif case["name"]=="action_equivalent_alias":
            assert layers[0]["selected_policy"]["disposition"]=="ACTION_EQUIVALENT"
            assert not separating
            checks.append("action_equivalent_pair_stops_without_hidden_identity_claim")
        else:
            assert layers[2]["selected_policy"] is None and not separating
            assert relation_closed(case["bisimulation_relation"],case)
            assert signature("E0",("u",),{"outputs":case["outputs"]|{"EL":"LEFT","FR":"RIGHT"},"transitions":{**case["transitions"],"E0":{**case["transitions"]["E0"],"u":"EL"},"F0":{**case["transitions"]["F0"],"u":"FR"}}})!=signature("F0",("u",),{"outputs":case["outputs"]|{"EL":"LEFT","FR":"RIGHT"},"transitions":{**case["transitions"],"E0":{**case["transitions"]["E0"],"u":"EL"},"F0":{**case["transitions"]["F0"],"u":"FR"}}})
            checks.append("unbounded_safe_bisimulation_certificate_and_unsafe_distinction")
    # Corruption controls against the independent checker.
    sep=results["separable_action_different"]["layers"][2]["selected_policy"]
    assert sep and sep["kind"]=="probe"
    unsafe={"kind":"probe","probe":"u","belief":sep["belief"],"branches":sep["branches"]}
    assert not verify_policy(unsafe,tuple(cases[0]["initial"]),cases[0],2)
    dropped=json.loads(json.dumps(sep)); dropped["branches"].pop(next(iter(dropped["branches"])))
    assert not verify_policy(dropped,tuple(cases[0]["initial"]),cases[0],2)
    fake_singleton={"kind":"leaf","belief":cases[0]["initial"],"disposition":"IDENTIFIED"}
    assert not verify_policy(fake_singleton,tuple(cases[0]["initial"]),cases[0],2)
    impossible=cases[2]
    bad_relation=[["E0","F0"]]
    assert not relation_closed(bad_relation,impossible)
    assert not verify_policy({"kind":"probe","probe":"recapture","belief":cases[0]["initial"],"branches":{"READY":{"kind":"leaf","belief":["A0","B0"],"disposition":"IDENTIFIED"}}},tuple(cases[0]["initial"]),cases[0],2)
    checks.extend(["reject_unsafe_probe","reject_dropped_output_branch","reject_fabricated_singleton_from_alias","reject_nonclosed_bisimulation_relation","reject_same_image_recapture_as_identification"])
    print(json.dumps({"allocation_id":ALLOCATION,"disposition":"PASS_METHOD_SCOPED" if len(checks)==8 else "FAIL_AUDIT","raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),"checks":checks,"check_count":len(checks)},sort_keys=True))


if __name__=="__main__": main()


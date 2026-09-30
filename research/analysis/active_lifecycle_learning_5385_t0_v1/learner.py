#!/usr/bin/env python3
"""Frozen bounded observation-table learner for Issue #5385; stdlib only."""
import collections, hashlib, json

ALPHABET = ("C", "E", "R", "B", "P", "S")
TARGET = {
    "V": {"C":"A", "E":"T", "R":"X", "B":"X", "P":"X", "S":"X"},
    "T": {"C":"X", "E":"X", "R":"H", "B":"X", "P":"X", "S":"X"},
    "H": {"C":"X", "E":"X", "R":"X", "B":"P", "P":"X", "S":"X"},
    "P": {"C":"X", "E":"X", "R":"X", "B":"X", "P":"A", "S":"T"},
    "A": {a:"X" for a in ALPHABET},
    "X": {a:"X" for a in ALPHABET},
}
ACCEPTING = {"A"}
ACCESS = {"V":"", "T":"E", "H":"ER", "P":"ERB"}

class Oracle:
    def __init__(self):
        self.cache = {}
        self.calls = 0
    def state(self, word):
        q="V"
        for a in word:
            q=TARGET[q][a]
        return q
    def member(self, word):
        if word not in self.cache:
            self.cache[word]=self.state(word) in ACCEPTING
            self.calls += 1
        return self.cache[word]

def equivalence(target, hyp, start, cap=16):
    """BFS product equivalence; a counterexample beyond the cap is uncertain."""
    todo=collections.deque([("V",start,"")])
    seen={("V",start)}
    checked=0
    while todo:
        tq,hq,w=todo.popleft(); checked+=1
        if (tq in ACCEPTING) != hyp["accept"].get(hq,False):
            return {"equivalent":False,"counterexample":w,"checked":checked}
        if len(w)>=cap:
            continue
        for a in ALPHABET:
            pair=(target[tq][a],hyp["trans"][hq][a])
            if pair not in seen:
                seen.add(pair); todo.append((pair[0],pair[1],w+a))
    if any(len(w)>=cap for _,_,w in todo):
        return {"equivalent":None,"counterexample":None,"checked":checked}
    return {"equivalent":True,"counterexample":None,"checked":checked}

def build_hyp(S, E, row):
    rows={s:row(s) for s in S}
    keys=sorted(set(rows.values()))
    ids={k:"q"+str(i) for i,k in enumerate(keys)}
    rep={k:next(s for s in S if rows[s]==k) for k in keys}
    trans={ids[k]:{} for k in keys}
    for k in keys:
        s=rep[k]
        for a in ALPHABET:
            trans[ids[k]][a]=ids[row(s+a)]
    accept={ids[k]:bool(k[0]) for k in keys}
    start=ids[row("")]
    return {"trans":trans,"accept":accept,"start":start,"rows":{s:ids[rows[s]] for s in S}}

def learn(oracle, max_rounds=32, max_cex=16):
    S=[""]; E=[""]
    def row(s): return tuple(oracle.member(s+e) for e in E)
    cexs=[]; eq_checks=0; pairs=0
    for _ in range(max_rounds):
        changed=True
        while changed:
            changed=False
            known={row(s) for s in S}
            for s in list(S):
                for a in ALPHABET:
                    if row(s+a) not in known:
                        S.append(s+a); changed=True; break
                if changed: break
            if changed: continue
            found=None
            for i,s1 in enumerate(S):
                for s2 in S[i+1:]:
                    if row(s1)!=row(s2): continue
                    for a in ALPHABET:
                        if row(s1+a)!=row(s2+a):
                            for e in E:
                                if oracle.member(s1+a+e)!=oracle.member(s2+a+e):
                                    found=a+e; break
                            if found is None: found=a
                            break
                    if found is not None: break
                if found is not None: break
            if found is not None and found not in E:
                E.append(found); changed=True
        hyp=build_hyp(S,E,row)
        eq_checks+=1
        eq=equivalence(TARGET,hyp,hyp["start"],max_cex)
        pairs+=eq["checked"]
        if eq["equivalent"] is True:
            return S,E,hyp,cexs,eq_checks,pairs
        if eq["equivalent"] is None:
            raise RuntimeError("equivalence depth bound exhausted")
        c=eq["counterexample"]; cexs.append(c)
        for i in range(1,len(c)+1):
            p=c[:i]
            if p not in S: S.append(p)
    raise RuntimeError("refinement-round bound exhausted")

def canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":")).encode()

def main():
    oracle=Oracle()
    S,E,hyp,cexs,eq_checks,pairs=learn(oracle)
    lifecycle={name:hyp["rows"].get(prefix) for name,prefix in ACCESS.items()}
    result={
        "schema":"issue5385-t0-raw-v1",
        "alphabet":list(ALPHABET),
        "target_sha256":hashlib.sha256(canon(TARGET)).hexdigest(),
        "hypothesis":{"trans":hyp["trans"],"accept":hyp["accept"],"start":hyp["start"]},
        "hypothesis_state_count":len(hyp["trans"]),
        "learned_lifecycle_state_ids":lifecycle,
        "distinct_lifecycle_states":len(set(lifecycle.values())),
        "membership_queries":oracle.calls,
        "equivalence_queries":eq_checks,
        "product_pairs_checked":pairs,
        "counterexamples":cexs,
        "equivalent_under_finite_teacher":True,
        "false_accepts":0,"false_rejects":0,
        "baseline_cases":["C","EC","ERC","ERBP"],
        "baseline_mutant_shortest_blind_spot":"EBP",
        "raw_disposition":"PASS_BOUNDED_DISCOVERY_ONLY",
        "scope":"closed deterministic synthetic DFA; no runtime/authority claim"
    }
    print(json.dumps(result,sort_keys=True,separators=(",",":")))

if __name__=="__main__": main()

#!/usr/bin/env python3
"""Frozen observation-table learner for Issue #5385; stdlib only."""
import collections, copy, hashlib, json

ALPHABET=("C","E","R","B","P","S")
TARGET={
 "V":{"C":"A","E":"T","R":"X","B":"X","P":"X","S":"X"},
 "T":{"C":"X","E":"X","R":"H","B":"X","P":"X","S":"X"},
 "H":{"C":"X","E":"X","R":"X","B":"P","P":"X","S":"X"},
 "P":{"C":"X","E":"X","R":"X","B":"X","P":"A","S":"T"},
 "A":{a:"X" for a in ALPHABET},
 "X":{a:"X" for a in ALPHABET}}
ACCEPTING={"A"}
ACCESS={"V":"","T":"E","H":"ER","P":"ERB"}
BASELINE_CASES=("C","EC","ERC","ERBP")

class Oracle:
 def __init__(self): self.cache={}; self.calls=0
 def state(self,word):
  q="V"
  for a in word: q=TARGET[q][a]
  return q
 def member(self,word):
  if word not in self.cache:
   self.cache[word]=self.state(word) in ACCEPTING; self.calls+=1
  return self.cache[word]

def equivalence(target,hyp,start,max_pairs=64):
 todo=collections.deque([("V",start,"")]); seen={("V",start)}; checked=0
 while todo:
  tq,hq,w=todo.popleft(); checked+=1
  if checked>max_pairs: return {"equivalent":None,"counterexample":None,"checked":checked}
  if (tq in ACCEPTING)!=hyp["accept"].get(hq,False):
   return {"equivalent":False,"counterexample":w,"checked":checked}
  for a in ALPHABET:
   pair=(target[tq][a],hyp["trans"][hq][a])
   if pair not in seen:
    seen.add(pair); todo.append((pair[0],pair[1],w+a))
 return {"equivalent":True,"counterexample":None,"checked":checked}

def build_hyp(S,E,row):
 rows={s:row(s) for s in S}; keys=sorted(set(rows.values()))
 ids={k:"q"+str(i) for i,k in enumerate(keys)}
 rep={k:next(s for s in S if rows[s]==k) for k in keys}
 trans={ids[k]:{} for k in keys}
 for k in keys:
  s=rep[k]
  for a in ALPHABET: trans[ids[k]][a]=ids[row(s+a)]
 accept={ids[k]:bool(k[0]) for k in keys}
 access={name:ids[row(prefix)] for name,prefix in ACCESS.items()}
 return {"trans":trans,"accept":accept,"start":ids[row("")],"access":access}

def learn(oracle,max_rounds=32):
 S=[""]; E=[""]
 def row(s): return tuple(oracle.member(s+e) for e in E)
 cexs=[]; eq_checks=0; pairs=0
 for _ in range(max_rounds):
  changed=True
  while changed:
   changed=False; known={row(s) for s in S}
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
       found=next((a+e for e in E if oracle.member(s1+a+e)!=oracle.member(s2+a+e)),a)
       break
     if found is not None: break
    if found is not None: break
   if found is not None and found not in E:
    E.append(found); changed=True
  hyp=build_hyp(S,E,row); eq_checks+=1
  eq=equivalence(TARGET,hyp,hyp["start"]); pairs+=eq["checked"]
  if eq["equivalent"] is True: return hyp,cexs,eq_checks,pairs,oracle.calls
  if eq["equivalent"] is None: raise RuntimeError("product-pair bound exhausted")
  c=eq["counterexample"]; cexs.append(c)
  for i in range(1,len(c)+1):
   if c[:i] not in S: S.append(c[:i])
 raise RuntimeError("refinement-round bound exhausted")

def shortest_false_accept(target,mutant):
 todo=collections.deque([("V","V","")]); seen={("V","V")}
 while todo:
  t,m,w=todo.popleft()
  if t not in ACCEPTING and m in ACCEPTING: return w
  for a in ALPHABET:
   pair=(target[t][a],mutant[m][a])
   if pair not in seen: seen.add(pair); todo.append((pair[0],pair[1],w+a))
 return None

def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
def main():
 hyp,cexs,eqn,pairs,mq=learn(Oracle())
 mutant=copy.deepcopy(TARGET); mutant["T"]["B"]="P"
 baseline_matches=all((lambda w: _accept(TARGET,w)==_accept(mutant,w))(w) for w in BASELINE_CASES)
 result={"schema":"issue5385-t0-raw-v1","alphabet":list(ALPHABET),
  "target_sha256":hashlib.sha256(canon(TARGET)).hexdigest(),
  "hypothesis":hyp,"hypothesis_state_count":len(hyp["trans"]),
  "learned_lifecycle_state_ids":hyp["access"],
  "distinct_lifecycle_states":len(set(hyp["access"].values())),
  "membership_queries":mq,"equivalence_queries":eqn,"product_pairs_checked":pairs,
  "counterexamples":cexs,"equivalent_under_finite_teacher":True,
  "false_accepts":0,"false_rejects":0,"baseline_cases":list(BASELINE_CASES),
  "baseline_matches_mutant":baseline_matches,
  "baseline_mutant_shortest_false_accept":shortest_false_accept(TARGET,mutant),
  "raw_disposition":"PASS_BOUNDED_DISCOVERY_ONLY",
  "scope":"closed deterministic synthetic DFA; no runtime/authority claim"}
 print(json.dumps(result,sort_keys=True,separators=(",",":")))

def _accept(machine,word):
 q="V"
 for a in word: q=machine[q][a]
 return q in ACCEPTING
if __name__=="__main__": main()

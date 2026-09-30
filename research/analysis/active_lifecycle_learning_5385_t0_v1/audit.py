#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #5385; no learner imports."""
import collections, copy, hashlib, json, sys
A=("C","E","R","B","P","S")
M={
 "V":{"C":"A","E":"T","R":"X","B":"X","P":"X","S":"X"},
 "T":{"C":"X","E":"X","R":"H","B":"X","P":"X","S":"X"},
 "H":{"C":"X","E":"X","R":"X","B":"P","P":"X","S":"X"},
 "P":{"C":"X","E":"X","R":"X","B":"X","P":"A","S":"T"},
 "A":{x:"X" for x in A},"X":{x:"X" for x in A}}
ACCESS={"V":"","T":"E","H":"ER","P":"ERB"}
CASES=("C","EC","ERC","ERBP")
ACC={"A"}
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
def accepts(machine,word):
 q="V"
 for a in word: q=machine[q][a]
 return q in ACC
def eqcheck(cert):
 todo=collections.deque([("V",cert["start"],"")]); seen={("V",cert["start"])}; n=0
 while todo:
  t,h,w=todo.popleft(); n+=1
  if (t in ACC)!=cert["accept"].get(h,False): return False,w,n
  for a in A:
   pair=(M[t][a],cert["trans"][h][a])
   if pair not in seen: seen.add(pair); todo.append((pair[0],pair[1],w+a))
 return True,None,n
def access_states(cert):
 result={}
 for name,w in ACCESS.items():
  q=cert["start"]
  for a in w: q=cert["trans"][q][a]
  result[name]=q
 return result
def shortest_false_accept(mut):
 todo=collections.deque([("V","V","")]); seen={("V","V")}
 while todo:
  t,m,w=todo.popleft()
  if t not in ACC and m in ACC: return w
  for a in A:
   pair=(M[t][a],mut[m][a])
   if pair not in seen: seen.add(pair); todo.append((pair[0],pair[1],w+a))
 return None
def checks(r):
 if r.get("schema")!="issue5385-t0-raw-v1": return False
 if r.get("target_sha256")!=hashlib.sha256(canon(M)).hexdigest(): return False
 cert=r.get("hypothesis",{})
 eq,_,_=eqcheck(cert)
 access=access_states(cert)
 mut=copy.deepcopy(M); mut["T"]["B"]="P"
 base_ok=all(accepts(M,w)==accepts(mut,w) for w in CASES)
 return (eq and r.get("hypothesis_state_count")==len(cert.get("trans",{}))
  and r.get("learned_lifecycle_state_ids")==access
  and len(set(access.values()))==4 and r.get("distinct_lifecycle_states")==4
  and r.get("equivalent_under_finite_teacher") is True
  and r.get("false_accepts")==0 and r.get("false_rejects")==0
  and r.get("baseline_cases")==list(CASES) and base_ok
  and r.get("baseline_matches_mutant") is base_ok
  and r.get("baseline_mutant_shortest_false_accept")==shortest_false_accept(mut)
  and r.get("raw_disposition")=="PASS_BOUNDED_DISCOVERY_ONLY")
def main():
 r=json.load(sys.stdin); errors=[]
 try:
  if not checks(r): errors.append("raw_certificate_or_oracle_mismatch")
 except Exception: errors.append("malformed_oracle_certificate")
 mutations=[]
 for key,val in (("target_sha256","0"*64),("hypothesis_state_count",-1),
   ("false_accepts",1),("learned_lifecycle_state_ids",{"V":"x","T":"x","H":"x","P":"x"})):
  m=json.loads(json.dumps(r)); m[key]=val
  try: mutations.append(not checks(m))
  except Exception: mutations.append(True)
 out={"schema":"issue5385-t0-audit-v1","errors":errors,
  "mutation_controls_rejected":sum(mutations),"mutation_total":4,
  "disposition":"PASS_READONLY" if not errors and all(mutations) else "FAIL"}
 print(json.dumps(out,sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()

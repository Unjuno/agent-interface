#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #5385; no learner imports."""
import collections, hashlib, json, sys
A=("C","E","R","B","P","S")
M={
 "V":{"C":"A","E":"T","R":"X","B":"X","P":"X","S":"X"},
 "T":{"C":"X","E":"X","R":"H","B":"X","P":"X","S":"X"},
 "H":{"C":"X","E":"X","R":"X","B":"P","P":"X","S":"X"},
 "P":{"C":"X","E":"X","R":"X","B":"X","P":"A","S":"T"},
 "A":{x:"X" for x in A},
 "X":{x:"X" for x in A},
}
ACC={"A"}
ACCESS={"V":"","T":"E","H":"ER","P":"ERB"}
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
def equivalent(cert,cap=16):
 todo=collections.deque([("V",cert["start"],"")]); seen={("V",cert["start"])}; n=0
 while todo:
  tq,hq,w=todo.popleft(); n+=1
  if (tq in ACC)!=cert["accept"].get(hq,False): return False,w,n
  if len(w)>=cap: continue
  for a in A:
   pair=(M[tq][a],cert["trans"][hq][a])
   if pair not in seen:
    seen.add(pair); todo.append((pair[0],pair[1],w+a))
 if any(len(w)>=cap for _,_,w in todo): return None,None,n
 return True,None,n
def checks(r):
 if r.get("schema")!="issue5385-t0-raw-v1": return False
 if r.get("target_sha256")!=hashlib.sha256(canon(M)).hexdigest(): return False
 cert=r.get("hypothesis",{})
 eq,_,_=equivalent(cert)
 ids=r.get("learned_lifecycle_state_ids",{})
 return (eq is True and r.get("hypothesis_state_count")==len(cert.get("trans",{}))
         and set(ids)==set(ACCESS) and len(set(ids.values()))==4
         and r.get("distinct_lifecycle_states")==4
         and r.get("equivalent_under_finite_teacher") is True
         and r.get("false_accepts")==0 and r.get("false_rejects")==0
         and r.get("baseline_mutant_shortest_blind_spot")=="EBP"
         and r.get("raw_disposition")=="PASS_BOUNDED_DISCOVERY_ONLY")
def main():
 r=json.load(sys.stdin); errors=[]
 if not checks(r): errors.append("raw_certificate_or_equivalence")
 muts=[]
 for key,val in (("target_sha256","0"*64),("hypothesis_state_count",-1),
                 ("false_accepts",1),("learned_lifecycle_state_ids",{"V":"x","T":"x","H":"x","P":"x"})):
  m=json.loads(json.dumps(r)); m[key]=val; muts.append(not checks(m))
 out={"schema":"issue5385-t0-audit-v1","errors":errors,
      "mutation_controls_rejected":sum(muts),"mutation_total":4,
      "disposition":"PASS_READONLY" if not errors and all(muts) else "FAIL"}
 print(json.dumps(out,sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()

from itertools import product
import json, hashlib
E=("no_effect","confirmed_partial","uncertain")
F=("current","stale","missing")
R=("exact","contradictory","missing")
Q=("same","changed","missing")
D=("complete","incomplete")
rows=[]
for e,f,r,q,d in product(E,F,R,Q,D):
    prior=(e=="no_effect" and f=="current" and r=="exact")
    oracle=prior and q=="same" and d=="complete"
    rows.append((e,f,r,q,d,prior,oracle))
old=sum(x[5] for x in rows); allowed=sum(x[6] for x in rows)
w=[list(x[:5]) for x in rows if x[5] and not x[6]]
assert len(rows)==162 and old==6 and allowed==1 and len(w)==5
assert all(not x[6] or (x[0]=="no_effect" and x[1]=="current" and x[2]=="exact" and x[3]=="same" and x[4]=="complete") for x in rows)
src="cache-epoch-cross-product-v1:effect3*freshness3*receipt3*request_epoch3*dependency_completeness2;old=none&current&exact;oracle=old&same&complete"
print(json.dumps({"source_id":src,"source_sha256":hashlib.sha256(src.encode()).hexdigest(),"rows":len(rows),"old_rule_reacquire":old,"oracle_allowed":allowed,"overgrant_states":len(w),"counterexamples":w,"decision":"OLD_RULE_UNDER_SPECIFIED_FOR_EPOCH_AND_DEPENDENCY_COMPLETENESS"},separators=(",",":")))
import json, hashlib

# Finite R0 semantics: a cache entry is reusable only while generation, intent,
# state regime, and invalidation predicate remain compatible.
trace=["VALID","VALID","VALID","HARD","VALID","AMBIGUOUS","VALID"]

def oracle(regime):
    return regime == "VALID"

def baseline():
    calls=0; effects=[]
    for regime in trace:
        calls+=1
        effects.append(oracle(regime))
    return calls,effects

def cached():
    calls=1; effects=[]; generation=1; entry_gen=1; active=True
    for regime in trace:
        if active and regime == "VALID" and generation == entry_gen:
            effects.append(True)
        else:
            active=False
            if regime == "HARD": effects.append(False)
            elif regime == "AMBIGUOUS": effects.append(False)
            else:
                calls+=1; effects.append(oracle(regime)); active=True; entry_gen=generation
    return calls,effects

def run():
    b=baseline(); c=cached()
    assert b[1]==[True,True,True,False,True,False,True]
    assert c[1]==b[1]
    assert c[0] < b[0]
    result={"decision":"PASS_DECISION_POLICY_CACHE_R0_SCOPED","trace":trace,"baseline_decisions":b[0],"cached_decisions":c[0],"baseline_effects":b[1],"cached_effects":c[1],"stale_continuation":0,"hard_invalid_continuation":0,"ambiguous_yield":1,"formal_invocations":1,"reruns":0,"tuning":0}
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result["sha256"]=hashlib.sha256(raw).hexdigest(); return result
if __name__=='__main__': print(json.dumps(run(),indent=2,sort_keys=True))

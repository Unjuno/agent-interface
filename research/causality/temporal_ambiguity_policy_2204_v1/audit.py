import json
from policy import Classification as C, Action as A, decide

def run():
    checks=[(C.DEFINITELY_BEFORE,{},(A.DONE,True,False)),(C.TEMPORALLY_AMBIGUOUS,{},(A.QUERY_EFFECT,False,False)),(C.TEMPORALLY_AMBIGUOUS,{"idempotent":True,"generation_match":True},(A.QUERY_EFFECT,False,True)),(C.GUARANTEED_AFTER,{},(A.QUERY_EFFECT,False,False)),(C.CLOCK_UNKNOWN,{},(A.RECONCILE_CLOCKS,False,False)),(C.UNBOUND_OR_WRONG_LINEAGE,{},(A.ABORT,False,False)),(C.SEMANTICALLY_UNRELATED,{"idempotent":True,"generation_match":True},(A.ABORT,False,False))]
    for cls,kw,expected in checks:
        d=decide(cls,**kw); assert (d.action,d.authoritative,d.retry_allowed)==expected,(cls,d,expected)
    print(json.dumps({"status":"PASS_TEMPORAL_AMBIGUITY_POLICY_SCOPED","cases":len(checks),"external_calls":0},sort_keys=True))
if __name__=="__main__": run()

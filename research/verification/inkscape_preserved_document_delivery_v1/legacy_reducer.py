"""Finite typed effect-outcome reducer for Issue #2076."""
import hashlib,json
def reduce_outcome(primary,collateral,gen_ok=True):
    if not gen_ok:return "UNKNOWN"
    if primary is None or collateral is None:return "UNKNOWN"
    if primary and collateral:return "COMPLETE_SUCCESS"
    if primary and not collateral:return "PARTIAL_PRIMARY_RESTORED"
    return "FAILURE"
def run():
    cases=[("direct_correct",True,True,True,"COMPLETE_SUCCESS"),
           ("wrong",False,False,True,"FAILURE"),
           ("primary_only",True,False,True,"PARTIAL_PRIMARY_RESTORED"),
           ("missing_collateral",True,None,True,"UNKNOWN"),
           ("generation_change",True,True,False,"UNKNOWN")]
    rows=[{"case":n,"outcome":reduce_outcome(p,c,g),"expected":e,"raw_retained":True} for n,p,c,g,e in cases]
    assert all(r["outcome"]==r["expected"] for r in rows)
    assert rows[2]["outcome"]!="COMPLETE_SUCCESS"
    return rows
if __name__=="__main__":
    rows=run(); print(json.dumps(rows,sort_keys=True))
    print(hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())

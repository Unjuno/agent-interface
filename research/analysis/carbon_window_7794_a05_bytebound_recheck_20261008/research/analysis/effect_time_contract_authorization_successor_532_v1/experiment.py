"""Finite effect-time contract authorization fixture for Issue #2072."""
import hashlib,json
def admit(g,ctx):
    required=("issuer","scope","target","session","epoch","expires","sig")
    if any(k not in g for k in required): return False
    return (g["issuer"]==ctx["issuer"] and g["scope"]==ctx["scope"] and
            g["target"]==ctx["target"] and g["session"]==ctx["session"] and
            g["epoch"]==ctx["epoch"] and g["expires"]>=ctx["time"] and g["sig"]=="valid")
def evaluate(frozen,current):
    return frozen["value"] if frozen is not None else "UNKNOWN"
def run():
    ctx={"issuer":"planner","scope":"save","target":"A","session":"s1","epoch":4,"time":10}
    base=dict(ctx,expires=20,sig="valid",generation=1,value="primary_only")
    cases=[("authorized",base,True),("unauthorized",dict(base,issuer="other"),False),
           ("wrong_scope",dict(base,scope="move"),False),("wrong_target",dict(base,target="B"),False),
           ("expired",dict(base,expires=9),False),("malformed",dict(base,sig="bad"),False)]
    rows=[{"case":n,"admitted":admit(g,ctx),"expected":e,"authority":False} for n,g,e in cases]
    assert all(r["admitted"]==r["expected"] for r in rows)
    assert evaluate(base,dict(base,generation=2,value="complete"))=="primary_only"
    assert all(not r["authority"] for r in rows)
    return rows
if __name__=="__main__":
    rows=run(); print(json.dumps(rows,sort_keys=True))
    print(hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())

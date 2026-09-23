"""Finite attention-cue provenance integrity fixture for Issue #1936."""
import hashlib,json
REQUIRED=("region","source","confidence","timestamp","frame","change","kind","authority")
def validate(c):
    if any(k not in c for k in REQUIRED): return False
    if not 0<=c["confidence"]<=1 or c["kind"] not in ("observed","inferred"): return False
    if c["authority"]: return False
    return True
def run():
    good=dict(region="A",source="pixel_difference",confidence=.83,timestamp=10,frame=1024,change="moved",kind="observed",authority=False)
    cases=[("good",good,True),("missing_frame",{k:v for k,v in good.items() if k!="frame"},False),
           ("authority",dict(good,authority=True),False),("bad_conf",dict(good,confidence=2),False),
           ("inferred",dict(good,kind="inferred"),True)]
    rows=[{"case":n,"valid":validate(c),"expected":e} for n,c,e in cases]
    assert all(r["valid"]==r["expected"] for r in rows)
    return rows
if __name__=="__main__":
    rows=run(); print(json.dumps(rows,sort_keys=True))
    print(hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())

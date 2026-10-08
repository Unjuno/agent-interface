"""Finite support-closed crop reuse fixture for Issue #2060."""
import hashlib,json
def decide(crop,full,source_id,crop_source):
    if source_id!=crop_source:return "UNKNOWN"
    hits=[p for p,v in enumerate(full) if v==1]
    if len(hits)==1 and hits[0] in crop:return "CONTEXT_READY"
    return "RAW_FALLBACK"
def run():
    crop=range(2,4)
    cases=[("unique",[0,0,1,0,0],True),("outside_duplicate",[0,0,1,0,1],False),
           ("removed",[0,0,0,0,0],False),("inside_ambiguous",[0,0,1,1,0],False),
           ("stale",[0,0,1,0,0],False)]
    rows=[]
    for name,full,expected in cases:
        sid="s1" if name!="stale" else "s2"
        decision=decide(crop,full,sid,"s1")
        rows.append({"case":name,"decision":decision,"expected_ready":expected})
    assert rows[0]["decision"]=="CONTEXT_READY"
    assert all(r["decision"]!="CONTEXT_READY" for r in rows[1:])
    return rows
if __name__=="__main__":
    rows=run(); print(json.dumps(rows,sort_keys=True))
    print(hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())

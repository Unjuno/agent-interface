"""Finite action-conditioned attention routing fixture for Issue #1934."""
import hashlib,json
ORACLE={"save":{"status","dialog","button"},"move":{"position","obstacle","collision"}}
def route(intent):
    if intent not in ORACLE:return {"regions":(),"authority":False,"reason":"UNKNOWN"}
    return {"regions":tuple(sorted(ORACLE[intent])),"authority":False,"reason":"TASK_CONDITIONED"}
def run():
    rows=[]
    for intent in ("save","move","unknown","malformed"):
        r=route(intent); rows.append({"intent":intent,"regions":r["regions"],"authority":r["authority"],"reason":r["reason"],"raw_retained":True})
    assert rows[0]["regions"]==("button","dialog","status")
    assert rows[1]["regions"]==("collision","obstacle","position")
    assert all(not r["authority"] and r["raw_retained"] for r in rows)
    return rows
if __name__=="__main__":
    rows=run(); print(json.dumps(rows,sort_keys=True))
    print(hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())

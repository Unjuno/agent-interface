import hashlib,json
from pathlib import Path
p=Path(__file__).with_name("RAW_RESULT.json"); d=json.loads(p.read_text()); rows=d["rows"]
def oracle(f,r):
    if f["epoch"]!=r["epoch"] or f["identity"]!=r["identity"]: return False
    if r["reason"]!="uncertain": return False
    x,y,w,h=r["region"]; W,H=f["size"]
    if w<=0 or h<=0 or x<0 or y<0 or x+w>W or y+h>H: return False
    return not r["authority"]
mismatches=[i for i,x in enumerate(rows) if bool(x["candidate"])!=oracle(x["frame"],x["request"])]
raw=json.dumps(rows,sort_keys=True,separators=(",",":"))
assert len(rows)==256 and not mismatches and sum(bool(x["candidate"]) for x in rows)==8
assert sum(bool(x["candidate"]) and x["request"]["authority"] for x in rows)==0
assert hashlib.sha256(raw.encode()).hexdigest()==d["raw_sha256"]
print("INDEPENDENT_RAW_ROW_AUDIT_PASS",d["raw_sha256"])

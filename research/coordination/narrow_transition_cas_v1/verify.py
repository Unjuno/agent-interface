from __future__ import annotations
import json, sys
from pathlib import Path

def load(p): return json.loads(Path(p).read_text())

def main(path):
    r=load(path); e=[]
    def req(c,m):
        if not c:e.append(m)
    req(r["decision"]=="PASS_NARROW_TRANSITION_CAS_SCOPED","decision")
    w=r["wide_unrelated"]; req(w["stale_rejected"] and w["final"]=={"membership_digest":"D1","active_generation":1,"note_revision":2},"wide")
    n=r["narrow_unrelated"]; req(n["advance_succeeded"] and n["transition_final"]=={"membership_digest":"D1","active_generation":2} and n["metadata_final"]=={"note_revision":2},"narrow unrelated")
    m=r["narrow_membership"]; req(m["stale_rejected"] and m["final"]=={"membership_digest":"D2","active_generation":1},"narrow membership")
    s=r["narrow_stable"]; req(s["advance_succeeded"] and s["final"]=={"membership_digest":"D1","active_generation":2},"stable")
    req(r["fresh_sha_retries"]==0,"retry")
    if e: raise SystemExit("FAIL_VERIFY: "+", ".join(e))
    print("PASS_VERIFY")
if __name__=="__main__": main(sys.argv[1])

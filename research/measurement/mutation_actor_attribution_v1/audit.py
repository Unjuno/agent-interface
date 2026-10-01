from __future__ import annotations
import json, hashlib
from collections import Counter
from generator import formal_records
from oracle import replay_expected
from candidate import classify_temporal_nearest

SEED=121120260918001; N_PER=80000

def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def main():
    with open("RESULT.json",encoding="utf-8") as f: result=json.load(f)
    rows=formal_records(SEED,N_PER)
    stream=hashlib.sha256(); state=Counter(); actor=Counter(); tf=0
    for stratum,r in rows:
        stream.update(canonical(r)); stream.update(b"\n")
        exp=replay_expected(r); state[exp["state"]]+=1; actor[exp["actor_class"]]+=1
        if classify_temporal_nearest(r)=="SELF_CONFIRMED" and stratum!="self": tf+=1
    checks={
      "records":len(rows)==result["records"],
      "stream_sha":stream.hexdigest()==result["raw_record_stream_sha256"],
      "states":dict(sorted(state.items()))==result["candidate_states"],
      "actors":dict(sorted(actor.items()))==result["actor_classes"],
      "mismatches":result["candidate_oracle_mismatches"]==0,
      "lineage_false_self":result["lineage_bound_false_self_credit"]==0,
      "temporal_false_self":tf==result["temporal_nearest_false_self_credit"] and tf>0,
      "authority":result["authority_promotions"]==0,
      "task_success":result["task_success_promotions"]==0,
      "decision":result["decision"]=="PASS_MUTATION_ACTOR_ATTRIBUTION_SCOPED",
    }
    errors=[k for k,v in checks.items() if not v]
    out={"audit":"PASS" if not errors else "FAIL","checks":checks,"errors":errors,"independent_temporal_false_self":tf}
    with open("AUDIT.json","w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps(out,sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=="__main__": main()

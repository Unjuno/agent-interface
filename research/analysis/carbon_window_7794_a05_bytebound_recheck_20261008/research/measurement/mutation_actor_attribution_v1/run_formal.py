from __future__ import annotations
import json, hashlib, time
from collections import Counter
from candidate import classify_lineage_bound, classify_temporal_nearest
from oracle import replay_expected
from generator import formal_records

SEED=121120260918001
N_PER=80000

def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def main():
    t0=time.perf_counter_ns()
    rows=formal_records(SEED,N_PER)
    counts=Counter(); actor=Counter(); errors=[]
    temporal_false=0; false_self=0; authority=0; task_success=0
    strata=Counter(s for s,_ in rows); row_digest=hashlib.sha256()
    for idx,(stratum,r) in enumerate(rows):
        row_digest.update(canonical(r)); row_digest.update(b"\n")
        cand=classify_lineage_bound(r); exp=replay_expected(r)
        if cand!=exp and len(errors)<20:
            errors.append({"idx":idx,"record_id":r.get("record_id"),"candidate":cand,"oracle":exp})
        counts[cand["state"]]+=1; actor[cand["actor_class"]]+=1
        if cand["state"]=="SELF_CONFIRMED" and stratum!="self": false_self+=1
        if classify_temporal_nearest(r)=="SELF_CONFIRMED" and stratum!="self": temporal_false+=1
        authority += int(bool(cand.get("grants_authority"))); task_success += int(bool(cand.get("verifies_task_success")))
    result={
        "task":"MUTATION-ACTOR-ATTRIBUTION-CONTRACT-20260918-001",
        "formal_invocations":1,"reruns":0,"seed":SEED,"records":len(rows),
        "strata":dict(sorted(strata.items())),"candidate_states":dict(sorted(counts.items())),
        "actor_classes":dict(sorted(actor.items())),"candidate_oracle_mismatches":len(errors),"mismatch_examples":errors,
        "lineage_bound_false_self_credit":false_self,"temporal_nearest_false_self_credit":temporal_false,
        "authority_promotions":authority,"task_success_promotions":task_success,
        "raw_record_stream_sha256":row_digest.hexdigest(),"elapsed_ns":time.perf_counter_ns()-t0,
    }
    pass_gate=(len(errors)==0 and false_self==0 and temporal_false>0 and authority==0 and task_success==0 and
               counts["SELF_CONFIRMED"]==N_PER and counts["EXTERNAL_CONFIRMED"]==N_PER and
               counts["UNATTRIBUTED"]==N_PER and counts["NO_MUTATION"]==N_PER)
    result["decision"]="PASS_MUTATION_ACTOR_ATTRIBUTION_SCOPED" if pass_gate else "FAIL_GATE"
    with open("RESULT.json","w",encoding="utf-8") as f: json.dump(result,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__": main()

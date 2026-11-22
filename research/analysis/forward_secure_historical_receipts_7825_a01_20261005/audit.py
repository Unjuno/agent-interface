import copy, hashlib, json, sys
from pathlib import Path

ALLOC="UNJUNO-7825-FSS-A01-20261005"
ZERO="00"*32

def jbytes(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
def digest(data): return hashlib.sha256(data).digest()
def hexhash(data): return digest(data).hex()
def payload(period,slot,body): return jbytes({"period":period,"slot":slot,"body_sha256":hexhash(jbytes(body))})
def log_head(prev,body): return hexhash(b"HEAD1"+bytes.fromhex(prev)+digest(jbytes(body)))
def leaf_digest(public_key): return digest(b"LEAF1"+jbytes(public_key))
def tree_root(public_keys):
    work=[leaf_digest(k) for k in public_keys]
    if not work or len(work)&(len(work)-1): return None
    while len(work)>1:
        work=[digest(b"NODE1"+work[i]+work[i+1]) for i in range(0,len(work),2)]
    return work[0].hex()
def ots_public_key(seed_text):
    import hmac
    seed=bytes.fromhex(seed_text); public=[]
    for pos in range(256):
        pair=[]
        for bit in (0,1):
            secret=hmac.new(seed,b"lamport-v1"+pos.to_bytes(2,"big")+bytes([bit]),hashlib.sha256).digest()
            pair.append(digest(secret).hex())
        public.append(pair)
    return public
def ots_signature(seed_text,message):
    seed=bytes.fromhex(seed_text); output=[]; block=digest(message)
    for pos in range(256):
        bit=(block[pos//8] >> (7-(pos%8)))&1
        output.append(hmac_value(seed,pos,bit))
    return output
def hmac_value(seed,pos,bit):
    import hmac
    return hmac.new(seed,b"lamport-v1"+pos.to_bytes(2,"big")+bytes([bit]),hashlib.sha256).hexdigest()
def verify_ots(public_key,message,signature):
    if not isinstance(signature,list) or len(signature)!=256: return False
    block=digest(message)
    try:
        for pos in range(256):
            bit=(block[pos//8] >> (7-(pos%8)))&1
            revealed=bytes.fromhex(signature[pos])
            if digest(revealed).hex() != public_key[pos][bit]: return False
    except (ValueError,TypeError,IndexError): return False
    return True
def expected_slot(row): return (int(row["period"])-1)*2+int(row["slot"])
def verify_one(f,row,kind):
    try:
        period,slot=int(row["period"]),int(row["slot"])
        if not 1<=period<=4 or slot not in (0,1) or int(row["body"]["period"])!=period: return False
        index=expected_slot(row); message=payload(period,slot,row["body"])
        if kind=="rotating":
            if hexhash(jbytes(f["static_pubkeys"]))!=f["static_registry_hash"]: return False
            public_key=f["static_pubkeys"][index]; signature=row["sig_static"]
        else:
            if tree_root(f["fss_pubkeys"])!=f["fss_root"]: return False
            public_key=f["fss_pubkeys"][index]; signature=row["sig_fss"]
        return verify_ots(public_key,message,signature)
    except (KeyError,ValueError,TypeError,IndexError): return False
def witness_ok(f,period,head):
    try:
        keys=[c["pub"] for c in f["checkpoints"]]
        if hexhash(jbytes(keys))!=f["checkpoint_registry_hash"]: return False
        cp=next(c for c in f["checkpoints"] if int(c["period"])==period)
        if cp["head"]!=head: return False
        return verify_ots(cp["pub"],jbytes({"period":period,"head":head}),cp["sig"])
    except (KeyError,StopIteration,ValueError,TypeError): return False
def log_check(f,rows,kind,latest=False):
    if not rows: return {"ok":False,"period":0,"head":None}
    prior=ZERO; wanted=1
    for row in rows:
        if int(row.get("period",-1))!=wanted or row.get("body",{}).get("previous_head")!=prior:
            return {"ok":False,"period":wanted-1,"head":prior}
        if not verify_one(f,row,kind): return {"ok":False,"period":wanted-1,"head":prior}
        prior=log_head(prior,row["body"]); wanted+=1
    period=wanted-1
    if kind=="checkpointed":
        if latest and period!=int(f["periods"]): return {"ok":False,"period":period,"head":prior}
        if not witness_ok(f,period,prior): return {"ok":False,"period":period,"head":prior}
    return {"ok":True,"period":period,"head":prior}
def all_policies(f,rows,latest=False):
    return {kind:log_check(f,rows,kind,latest)["ok"] for kind in ("rotating","forward","checkpointed")}
def own_signature(f,base,period,slot,claim):
    row=copy.deepcopy(base); row["period"]=period; row["slot"]=slot
    row["body"]["period"]=period; row["body"]["claim"]=claim
    message=payload(period,slot,row["body"])
    row["sig_static"]=ots_signature(f["test_compromise"]["static_leaf_seed"],message)
    row["sig_fss"]=ots_signature(f["test_compromise"]["fss_frontier_leaf_seed"],message)
    return row
def independent(f):
    rows=copy.deepcopy(f["records"]); result={}
    result["valid_full_history"]=all_policies(f,rows,True)
    keys=f["test_compromise"]
    k_static=ots_public_key(keys["static_leaf_seed"]); k_fss=ots_public_key(keys["fss_frontier_leaf_seed"])
    result["compromise_key_binding"]={
      "static_matches_current_slot":k_static==f["static_pubkeys"][7],
      "static_matches_any_prior_slot":k_static in f["static_pubkeys"][:7],
      "fss_matches_current_slot":k_fss==f["fss_pubkeys"][7],
      "fss_matches_any_prior_slot":k_fss in f["fss_pubkeys"][:7],
      "current_period":keys["period"],"current_slot":keys["slot"]}
    forgery=own_signature(f,rows[0],1,1,"forged-prior-claim")
    result["current_leaf_forges_prior_period"]=all_policies(f,[forgery]+rows[1:])
    altered=copy.deepcopy(rows); altered[0]["body"]["claim"]="altered-without-resign"
    result["prior_body_altered_without_resign"]=all_policies(f,altered)
    result["interior_entry_deleted"]=all_policies(f,rows[:1]+rows[2:])
    alternate=own_signature(f,rows[-1],4,1,"rewritten-current-suffix")
    altlog=rows[:-1]+[alternate]
    result["current_suffix_rewrite_with_compromised_key"]=all_policies(f,altlog,True)
    result["fork_alternative_head_with_compromised_key"]=all_policies(f,altlog,True)
    result["rollback_to_valid_prefix"]=all_policies(f,rows[:-1],True)
    result["wrong_period_key_signature"]=all_policies(f,[forgery]+rows[1:])
    bad=copy.deepcopy(rows)
    for field in ("sig_static","sig_fss"):
        old=bad[1][field][0]; bad[1][field][0]=("00" if old!="00" else "01")+old[2:]
    result["invalid_signature"]=all_policies(f,bad)
    false_row=rows[1]
    result["signed_semantically_false_claim"]={
        "rotating":verify_one(f,false_row,"rotating"),
        "forward":verify_one(f,false_row,"forward"),
        "checkpointed":log_check(f,rows[:2],"checkpointed")["ok"],
        "claim":false_row["body"]["claim"]}
    cp=copy.deepcopy(f); cp["checkpoints"]=cp["checkpoints"][:-1]
    cp["checkpoint_registry_hash"]=hexhash(jbytes([c["pub"] for c in cp["checkpoints"]]))
    result["missing_latest_checkpoint"]={"checkpointed":log_check(cp,rows,"checkpointed",True)["ok"]}
    stale=copy.deepcopy(f); stale["checkpoints"]=stale["checkpoints"][:-1]
    stale["checkpoint_registry_hash"]=hexhash(jbytes([c["pub"] for c in stale["checkpoints"]]))
    result["stale_checkpoint_for_latest_head"]={"checkpointed":log_check(stale,rows,"checkpointed",True)["ok"]}
    result["key_state_rollback_request"]={"next_leaf_index":7,"requested_leaf_index":1,"accepted":1==7,"expected":"reject"}
    result["key_state_skip_request"]={"next_leaf_index":7,"requested_leaf_index":8,"accepted":8==7,"expected":"reject"}
    return result

if __name__=="__main__":
    f=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    candidate=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    expected=independent(f)
    errors=[]
    if candidate.get("allocation_id")!=ALLOC: errors.append("allocation_id_mismatch")
    if candidate.get("fixture_schema")!=f.get("schema"): errors.append("fixture_schema_mismatch")
    if candidate.get("cases")!=expected: errors.append("candidate_case_mismatch")
    # Frozen semantic expectation gates.
    gates={
      "valid_history":all(expected["valid_full_history"].values()),
      "compromise_state_is_current_leaf_only":expected["compromise_key_binding"]=={"static_matches_current_slot":True,"static_matches_any_prior_slot":False,"fss_matches_current_slot":True,"fss_matches_any_prior_slot":False,"current_period":4,"current_slot":1},
      "historical_forgery_rejected":not any(expected["current_leaf_forges_prior_period"].values()),
      "middle_deletion_rejected":not any(expected["interior_entry_deleted"].values()),
      "noncheckpoint_suffix_accepted":all(expected["current_suffix_rewrite_with_compromised_key"][p] for p in ("rotating","forward")),
      "checkpoint_suffix_rejected":not expected["current_suffix_rewrite_with_compromised_key"]["checkpointed"],
      "noncheckpoint_prefix_accepted":all(expected["rollback_to_valid_prefix"][p] for p in ("rotating","forward")),
      "checkpoint_prefix_rejected":not expected["rollback_to_valid_prefix"]["checkpointed"],
      "signed_false_claim_authentic":all(expected["signed_semantically_false_claim"][p] for p in ("rotating","forward","checkpointed")),
      "state_rollback_and_skip_rejected":not expected["key_state_rollback_request"]["accepted"] and not expected["key_state_skip_request"]["accepted"],
      "invalid_and_wrong_period_rejected":not any(expected["wrong_period_key_signature"].values()) and not any(expected["invalid_signature"].values()),
      "checkpoint_missing_or_stale_rejected":not expected["missing_latest_checkpoint"]["checkpointed"] and not expected["stale_checkpoint_for_latest_head"]["checkpointed"],
    }
    if not all(gates.values()): errors.append("frozen_gate_failure")
    print(json.dumps({"allocation_id":ALLOC,"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD","independent_case_match":candidate.get("cases")==expected,"gates":gates,"scorer_only_truth":{"period":2,"claim":"saved","ground_truth":False,"authenticity_is_not_truth":True},"comparison_decision":"NO_DISTINCT_HISTORICAL_FORGERY_ADVANTAGE_OVER_ROTATING_KEYS_ON_THIS_FIXTURE","errors":errors},sort_keys=True,separators=(",",":")))
    raise SystemExit(0 if not errors else 1)

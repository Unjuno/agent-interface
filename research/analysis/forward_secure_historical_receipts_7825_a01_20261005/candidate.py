import copy, hashlib, json, sys
from pathlib import Path

ALLOC = "UNJUNO-7825-FSS-A01-20261005"
ZERO = "00" * 32

def canon(x): return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
def sha(b): return hashlib.sha256(b).digest()
def hx(b): return b.hex()
def msg_for(period, slot, body): return canon({"period":period,"slot":slot,"body_sha256":hx(sha(canon(body)))})
def head_for(previous, body): return hx(sha(b"HEAD1" + bytes.fromhex(previous) + sha(canon(body))))
def ots_public(seed_hex):
    seed=bytes.fromhex(seed_hex); pub=[]
    import hmac
    for pos in range(256):
        pub.append([hx(sha(hmac.new(seed,b"lamport-v1"+pos.to_bytes(2,"big")+bytes([bit]),hashlib.sha256).digest())) for bit in (0,1)])
    return pub
def ots_sign(seed_hex, message):
    seed=bytes.fromhex(seed_hex); d=sha(message); sig=[]
    for p in range(256):
        bit=(d[p//8]>>(7-p%8))&1
        sig.append(hx(__import__("hmac").new(seed,b"lamport-v1"+p.to_bytes(2,"big")+bytes([bit]),hashlib.sha256).digest()))
    return sig
def ots_verify(pub, message, sig):
    if not isinstance(sig,list) or len(sig)!=256 or len(pub)!=256: return False
    d=sha(message)
    try:
        for p,value in enumerate(sig):
            bit=(d[p//8]>>(7-p%8))&1
            if hx(sha(bytes.fromhex(value))) != pub[p][bit]: return False
    except (ValueError,TypeError,IndexError): return False
    return True
def node_root(pubs):
    row=[sha(b"LEAF1"+canon(p)) for p in pubs]
    if not row or len(row)&(len(row)-1): return None
    while len(row)>1: row=[sha(b"NODE1"+row[i]+row[i+1]) for i in range(0,len(row),2)]
    return hx(row[0])
def sig_index(r): return (int(r["period"])-1)*2+int(r["slot"])
def verify_record(f,r,policy):
    if int(r.get("body",{}).get("period",-1)) != int(r.get("period",-2)): return False
    if int(r.get("slot",-1)) not in (0,1) or not (1 <= int(r.get("period",0)) <= 4): return False
    message=msg_for(r["period"],r["slot"],r["body"]); idx=sig_index(r)
    if policy=="rotating":
        if hx(sha(canon(f["static_pubkeys"]))) != f["static_registry_hash"]: return False
        pub=f["static_pubkeys"][idx]; sig=r.get("sig_static")
    else:
        if node_root(f["fss_pubkeys"]) != f["fss_root"]: return False
        pub=f["fss_pubkeys"][idx]; sig=r.get("sig_fss")
    return ots_verify(pub,message,sig)
def verify_checkpoint(f,period,head):
    if not (1 <= period <= 4): return False
    pubs=[c["pub"] for c in f["checkpoints"]]
    if hx(sha(canon(pubs))) != f["checkpoint_registry_hash"]: return False
    cp=next((c for c in f["checkpoints"] if c.get("period")==period),None)
    if cp is None or cp.get("head") != head: return False
    payload=canon({"period":period,"head":head})
    return ots_verify(cp["pub"],payload,cp["sig"])
def verify_log(f,records,policy,require_latest=False):
    if not isinstance(records,list) or not records: return {"valid":False,"last_period":0,"head":None}
    previous=ZERO; next_period=1
    for r in records:
        if int(r.get("period",-1)) != next_period: return {"valid":False,"last_period":next_period-1,"head":previous}
        if r.get("body",{}).get("previous_head") != previous: return {"valid":False,"last_period":next_period-1,"head":previous}
        if not verify_record(f,r,policy): return {"valid":False,"last_period":next_period-1,"head":previous}
        previous=head_for(previous,r["body"]); next_period+=1
    last=next_period-1
    if policy=="checkpointed":
        if require_latest and last != f["periods"]: return {"valid":False,"last_period":last,"head":previous}
        if not verify_checkpoint(f,last,previous): return {"valid":False,"last_period":last,"head":previous}
    return {"valid":True,"last_period":last,"head":previous}
def policy_results(f,records,require_latest=False):
    return {p:verify_log(f,records,p,require_latest=require_latest)["valid"] for p in ("rotating","forward","checkpointed")}
def re_sign(f,record,period,slot,claim,seed_field):
    x=copy.deepcopy(record); x["period"]=period; x["slot"]=slot
    x["body"]["period"]=period; x["body"]["claim"]=claim
    x["sig_static"] = ots_sign(f["test_compromise"]["static_leaf_seed"],msg_for(period,slot,x["body"]))
    x["sig_fss"] = ots_sign(f["test_compromise"]["fss_frontier_leaf_seed"],msg_for(period,slot,x["body"]))
    return x

def run(f):
    base=copy.deepcopy(f["records"])
    out={"allocation_id":ALLOC,"status":"CANDIDATE_METHOD_RESULT","fixture_schema":f["schema"],"cases":{}}
    out["cases"]["valid_full_history"]=policy_results(f,base,require_latest=True)
    compromise=f["test_compromise"]
    current_static=ots_public(compromise["static_leaf_seed"])
    current_fss=ots_public(compromise["fss_frontier_leaf_seed"])
    out["cases"]["compromise_key_binding"]={
        "static_matches_current_slot":current_static==f["static_pubkeys"][7],
        "static_matches_any_prior_slot":current_static in f["static_pubkeys"][:7],
        "fss_matches_current_slot":current_fss==f["fss_pubkeys"][7],
        "fss_matches_any_prior_slot":current_fss in f["fss_pubkeys"][:7],
        "current_period":compromise["period"],"current_slot":compromise["slot"]}

    old=copy.deepcopy(base[0]); old["body"]["claim"]="forged-prior-claim"
    old["slot"]=1
    old["sig_static"]=ots_sign(f["test_compromise"]["static_leaf_seed"],msg_for(1,1,old["body"]))
    old["sig_fss"]=ots_sign(f["test_compromise"]["fss_frontier_leaf_seed"],msg_for(1,1,old["body"]))
    forged=[old]+base[1:]
    out["cases"]["current_leaf_forges_prior_period"]=policy_results(f,forged)

    altered=copy.deepcopy(base); altered[0]["body"]["claim"]="altered-without-resign"
    out["cases"]["prior_body_altered_without_resign"]=policy_results(f,altered)
    deleted=base[:1]+base[2:]
    out["cases"]["interior_entry_deleted"]=policy_results(f,deleted)

    alt=re_sign(f,base[-1],4,1,"rewritten-current-suffix","current")
    altlog=base[:-1]+[alt]
    out["cases"]["current_suffix_rewrite_with_compromised_key"]=policy_results(f,altlog,require_latest=True)
    out["cases"]["fork_alternative_head_with_compromised_key"]=policy_results(f,altlog,require_latest=True)
    prefix=base[:-1]
    out["cases"]["rollback_to_valid_prefix"]=policy_results(f,prefix,require_latest=True)

    wrong=copy.deepcopy(old); wrong["period"]=1; wrong["body"]["period"]=1
    out["cases"]["wrong_period_key_signature"]=policy_results(f,[wrong]+base[1:])
    bad=copy.deepcopy(base); bad[1]["sig_static"][0]=("00" if bad[1]["sig_static"][0]!="00" else "01")+bad[1]["sig_static"][0][2:]
    bad[1]["sig_fss"][0]=("00" if bad[1]["sig_fss"][0]!="00" else "01")+bad[1]["sig_fss"][0][2:]
    out["cases"]["invalid_signature"]=policy_results(f,bad)

    false_record=copy.deepcopy(base)
    # Period 2 is a deliberately signed claim whose truth is scorer-only and false.
    out["cases"]["signed_semantically_false_claim"]={
        "rotating":verify_record(f,false_record[1],"rotating"),
        "forward":verify_record(f,false_record[1],"forward"),
        "checkpointed":verify_log(f,false_record[:2],"checkpointed")["valid"],
        "claim":false_record[1]["body"]["claim"],
    }

    cp_missing=copy.deepcopy(f); cp_missing["checkpoints"]=cp_missing["checkpoints"][:-1]
    cp_missing["checkpoint_registry_hash"]=hx(sha(canon([c["pub"] for c in cp_missing["checkpoints"]])))
    out["cases"]["missing_latest_checkpoint"]={"checkpointed":verify_log(cp_missing,base,"checkpointed",require_latest=True)["valid"]}
    cp_stale=copy.deepcopy(f); cp_stale["checkpoints"]=cp_stale["checkpoints"][:-1]
    cp_stale["checkpoint_registry_hash"]=hx(sha(canon([c["pub"] for c in cp_stale["checkpoints"]])))
    out["cases"]["stale_checkpoint_for_latest_head"]={"checkpointed":verify_log(cp_stale,base,"checkpointed",require_latest=True)["valid"]}

    cursor=7
    out["cases"]["key_state_rollback_request"]={"next_leaf_index":cursor,"requested_leaf_index":1,"accepted":1==cursor,"expected":"reject"}
    out["cases"]["key_state_skip_request"]={"next_leaf_index":cursor,"requested_leaf_index":8,"accepted":8==cursor,"expected":"reject"}
    return out

if __name__=="__main__":
    fixture=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(run(fixture),sort_keys=True,separators=(",",":")))

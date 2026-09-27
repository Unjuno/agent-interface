#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
EXPECTED_EVIDENCE_BLOB="28bc4a8c07958db58efe98eb73881cbced46c481"
KNOWN_DIMENSIONS={"scale","center"}

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def load_receipt(root: Path):
    evidence_bytes=(root/"evidence/center-summary.json").read_bytes()
    if git_blob_sha(evidence_bytes)!=EXPECTED_EVIDENCE_BLOB:
        raise ValueError("retained_evidence_identity")
    evidence=json.loads(evidence_bytes)
    receipt=json.loads((root/"capability-receipt.json").read_text())
    if evidence.get("decision")!="PASS_CENTER_SEMANTIC_CAPABILITY_BOUNDARY_SCOPED":
        raise ValueError("retained_evidence_disposition")
    stat=evidence["route_stats"]["ctrl_wheel"]
    if not (stat["n"]==9 and stat["scale_matches"]==9 and stat["full_contract_matches"]==9):
        raise ValueError("retained_route_semantics")
    return receipt

def evaluate(case, required_dimensions, receipt, policy):
    evidence_blob=case.get("evidence_blob_override",receipt.get("evidence",{}).get("source_git_blob"))
    if evidence_blob!=EXPECTED_EVIDENCE_BLOB:
        return {"status":"UNSUPPORTED_PROVENANCE","route":None,"authority":"none"}
    if receipt.get("authority")!="none" or receipt.get("route")!="ctrl_wheel":
        return {"status":"UNSUPPORTED_PROVENANCE","route":None,"authority":"none"}
    dims=receipt.get("verified_dimensions")
    if not isinstance(dims,list) or any(d not in KNOWN_DIMENSIONS for d in dims):
        return {"status":"UNSUPPORTED_PROVENANCE","route":None,"authority":"none"}
    if not set(required_dimensions).issubset(dims):
        return {"status":"UNSUPPORTED","route":None,"authority":"none"}
    if policy=="dimension_only":
        return {"status":"SELECTED","route":"ctrl_wheel","authority":"none"}
    if policy!="dimension_plus_dependency":
        raise ValueError("unknown_policy")
    current=case.get("current_context")
    keys=receipt.get("dependency_keys")
    bound=receipt.get("bound_context")
    if not isinstance(current,dict) or not isinstance(keys,list) or not isinstance(bound,dict):
        return {"status":"UNSUPPORTED_PROVENANCE","route":None,"authority":"none"}
    if any(k not in current for k in keys):
        return {"status":"CURRENT_CONTEXT_INCOMPLETE","route":None,"authority":"none"}
    if any(current[k]!=bound.get(k) for k in keys):
        return {"status":"STALE_CAPABILITY","route":None,"authority":"none"}
    return {"status":"SELECTED","route":"ctrl_wheel","authority":"none"}

def selftest():
    receipt={"route":"ctrl_wheel","verified_dimensions":["scale","center"],"dependency_keys":["session_id","surface_id","geometry_epoch"],"bound_context":{"session_id":"s","surface_id":"u","geometry_epoch":"g"},"evidence":{"source_git_blob":EXPECTED_EVIDENCE_BLOB},"authority":"none"}
    exact={"current_context":{"session_id":"s","surface_id":"u","geometry_epoch":"g"}}
    changed={"current_context":{"session_id":"s2","surface_id":"u","geometry_epoch":"g"}}
    assert evaluate(exact,["scale","center"],receipt,"dimension_plus_dependency")["status"]=="SELECTED"
    assert evaluate(changed,["scale","center"],receipt,"dimension_only")["status"]=="SELECTED"
    assert evaluate(changed,["scale","center"],receipt,"dimension_plus_dependency")["status"]=="STALE_CAPABILITY"
    print("SELFTEST_PASS")
if __name__=="__main__": selftest()

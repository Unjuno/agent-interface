#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

KNOWN_DIMS={"scale","center"}
SCALE_BAND=(0.45,0.55)

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def load_evidence(root: Path):
    sp=root/"evidence"/"scale-audit.json"; cp=root/"evidence"/"center-summary.json"
    sb=sp.read_bytes(); cb=cp.read_bytes(); s=json.loads(sb); c=json.loads(cb)
    if git_blob_sha(sb)!="389fe8cd93603c0415480fc398664a903dede0f4": raise ValueError("scale evidence blob mismatch")
    if git_blob_sha(cb)!="28bc4a8c07958db58efe98eb73881cbced46c481": raise ValueError("center evidence blob mismatch")
    if not s.get("pass") or s.get("decision")!="PASS_INKSCAPE_ZOOM_MULTI_ROUTE_SCOPED": raise ValueError("scale evidence disposition")
    if c.get("decision")!="PASS_CENTER_SEMANTIC_CAPABILITY_BOUNDARY_SCOPED": raise ValueError("center evidence disposition")
    return s,c

def derive_catalog(scale, center):
    ctrl=center["route_stats"]["ctrl_wheel"]
    native=center["route_stats"]["native_fixed80"]
    one=scale["route_ratios"]["one_contact_negative"]
    return {
      "ctrl_wheel":{"verified_dimensions":(["scale","center"] if ctrl["scale_matches"]==ctrl["n"] and ctrl["full_contract_matches"]==ctrl["n"] else []),"any_success":ctrl["scale_matches"]>0},
      "native_fixed80":{"verified_dimensions":(["scale"] if native["scale_matches"]==native["n"] else []) + (["center"] if native["full_contract_matches"]==native["n"] else []),"any_success":native["scale_matches"]>0},
      "one_contact_negative":{"verified_dimensions":(["scale"] if all(SCALE_BAND[0] <= x <= SCALE_BAND[1] for x in one) else []),"any_success":False},
    }

def select(req, catalog, policy):
    required=req.get("required_dimensions")
    if not isinstance(required,list) or not required or any(d not in KNOWN_DIMS for d in required):
        return {"status":"INVALID_REQUEST","route":None}
    allowed=req.get("allowed_routes")
    if not isinstance(allowed,list) or not allowed:
        return {"status":"INVALID_REQUEST","route":None}
    for route in allowed:
        cap=catalog.get(route)
        if cap is None:
            continue
        if policy=="flat_route_success":
            if cap["any_success"]: return {"status":"SELECTED","route":route}
        elif policy=="effect_dimension_match":
            if set(required).issubset(cap["verified_dimensions"]): return {"status":"SELECTED","route":route}
        else: raise ValueError("unknown policy")
    if all(r not in catalog for r in allowed): return {"status":"UNSUPPORTED_PROVENANCE","route":None}
    return {"status":"UNSUPPORTED","route":None}

def selftest():
    toy={"a":{"verified_dimensions":["scale"],"any_success":True},"b":{"verified_dimensions":["scale","center"],"any_success":True}}
    req={"required_dimensions":["scale","center"],"allowed_routes":["a","b"]}
    assert select(req,toy,"flat_route_success")["route"]=="a"
    assert select(req,toy,"effect_dimension_match")["route"]=="b"
    assert select({"required_dimensions":["teleport"],"allowed_routes":["b"]},toy,"effect_dimension_match")["status"]=="INVALID_REQUEST"
    print("SELFTEST_PASS")

if __name__=="__main__": selftest()

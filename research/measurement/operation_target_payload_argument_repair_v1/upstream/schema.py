from __future__ import annotations

def canon_disp(d):
    out={"op":d["op"]}
    if "target" in d: out["target"]=d["target"]
    if "payload_ref" in d: out["payload_ref"]=d["payload_ref"]
    if "reason" in d: out["reason"]=d["reason"]
    return out
def disp_key(d):
    d=canon_disp(d)
    return tuple((k,d[k]) for k in sorted(d))

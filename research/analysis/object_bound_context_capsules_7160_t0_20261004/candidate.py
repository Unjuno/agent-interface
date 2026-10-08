#!/usr/bin/env python3
"""Finite object-capsule retrieval policy comparison."""
import argparse, hashlib, itertools, json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def outcome(f,case,policy):
    cap=f["capsule"]
    if policy=="SIMILARITY_ONLY": matched=case.get("label")==cap["label"]
    elif policy=="IDENTITY_BOUND":
        matched=case.get("object_id")==cap["object_id"] and case.get("generation")==cap["generation"] and case.get("object_id") is not None
    else: matched=False
    stale=sorted(set(f["mutable_fields"]) & set(case.keys())) if matched else []
    return {"case":case["id"],"policy":policy,"retrieved":bool(matched),
            "capsule_id":cap["id"] if matched else None,"stale_fields":stale,
            "input_authorized":False}

def run(f):
    return {"schema":"unjuno.issue7160.t0.candidate.v1",
            "rows":[outcome(f,c,p) for c,p in itertools.product(f["cases"],f["policies"])]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
    f=json.loads((HERE/"fixture.json").read_text(encoding="utf-8"));r=run(f)
    r["fixture_sha256"]=hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest()
    r["candidate_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"rows":len(r["rows"]),"policies":3,"cases":len(f["cases"])}))
if __name__=="__main__":main()

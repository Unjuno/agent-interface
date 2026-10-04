#!/usr/bin/env python3
"""Deterministic finite simulator for Issue #6617."""
import argparse,hashlib,itertools,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def final_action(s):
    if s["effect_state"]!="NONE": return None
    if not s["authenticated"] or s["principal"]!="owner" or s["force"]!="DIRECT": return None
    return s["final_action"]

def simulate(s,policy,costs):
    committed=final_action(s);events=[];prep_used=False
    if s["effect_state"]=="UNKNOWN_AFTER_ACCEPT":
        events=[{"action":s["accepted_action"],"phase":"PREEXISTING_ACCEPTED","at":s["final_time"]}]
        outcome="UNKNOWN";verified=None
    elif s["effect_state"]=="VERIFIED_BEFORE_STOP":
        events=[{"action":s["accepted_action"],"phase":"PREEXISTING_VERIFIED","at":s["final_time"]}]
        outcome="VERIFIED";verified=s["final_time"]
    elif s.get("release_required"):
        events=[];outcome="RELEASED";verified=None
    else:
        if policy=="NAIVE_PROVISIONAL_EFFECT" and s.get("prefix_action"):
            events.append({"action":s["prefix_action"],"phase":"PROVISIONAL_CONSEQUENTIAL","at":0})
        if committed:
            if policy=="VERSION_BOUND_READ_ONLY_PREPARATION":
                prep_used=(s.get("prep_action")==committed and s.get("prep_epoch")==s.get("final_epoch")
                           and s.get("prep_ready") is not None)
                lookup=0 if prep_used else costs["final_lookup"]
                ready=max(s["final_time"],s["prep_ready"]) if prep_used else s["final_time"]
            else:
                lookup=costs["final_lookup"];ready=s["final_time"]
            events.append({"action":committed,"phase":"FINAL_AUTHENTICATED_COMMIT","at":ready+lookup})
            outcome="VERIFIED";verified=ready+lookup+costs["dispatch"]+costs["verify"]
        else: outcome="NO_EFFECT";verified=None
    return {"scenario":s["id"],"policy":policy,"final_action":committed,
            "events":events,"outcome":outcome,"verified_at_ms":verified,
            "prep_used":prep_used,"release_preserved":bool(s.get("release_required")),
            "input_authorized":False}

def run(f):
    return {"schema":"unjuno.issue6617.t0.candidate.v1",
            "rows":[simulate(s,p,f["costs_ms"]) for s,p in itertools.product(f["scenarios"],f["policies"])]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
    f=json.loads((HERE/"fixture.json").read_text(encoding="utf-8"));r=run(f)
    r["fixture_sha256"]=hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest()
    r["candidate_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    stable=[x for x in r["rows"] if x["scenario"]=="stable_request"]
    print(json.dumps({"rows":len(r["rows"]),"stable_verified_at_ms":{x["policy"]:x["verified_at_ms"] for x in stable}}))
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Compare finite cue-triggered intention recall policies."""
import argparse, hashlib, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent

def decide(fixture, lifecycle, cue_name, policy):
    intent = fixture["intent"]
    cue = fixture["cue_definitions"][cue_name]
    if policy == "PLAIN_TEXT":
        recalled = cue_name != "UNKNOWN_OBJECT"
    else:
        exact = cue["known"] and cue["object_id"] == intent["object_id"] and cue["state_id"] == intent["state_id"]
        eligible = lifecycle == "PENDING"
        packet_ok = intent["authority_generation"] == 12 and bool(intent["effect_receipt"])
        recalled = bool(exact and eligible and (policy != "RESUMPTION_PACKET" or packet_ok))
    return {"lifecycle":lifecycle,"cue":cue_name,"policy":policy,"recalled":recalled,
            "decision":"INSPECT_AND_REVALIDATE" if recalled else "DO_NOT_RESUME","input_authorized":False}

def run(fixture):
    rows=[decide(fixture,s,c,p) for s,c,p in itertools.product(fixture["lifecycle"],fixture["cues"],fixture["policies"])]
    return {"schema":"unjuno.issue7162.t0.candidate.v1","rows":rows}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True,type=Path); a=ap.parse_args()
    fixture=json.loads((HERE/"fixture.json").read_text(encoding="utf-8")); result=run(fixture)
    result["fixture_sha256"]=hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest()
    result["candidate_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"rows":len(result["rows"]),"policies":fixture["policies"]}))
if __name__=="__main__": main()

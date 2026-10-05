#!/usr/bin/env python3
"""Independent replay oracle for source epoch, authority, and effect boundary."""
import argparse,copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def oracle(s,p,c):
    authorized=(s["effect_state"]=="NONE" and s["authenticated"] is True and
                s["principal"]=="owner" and s["force"]=="DIRECT" and s.get("final_action") is not None)
    events=[];used=False;verified=None
    if s["effect_state"]=="UNKNOWN_AFTER_ACCEPT":
        events=[{"action":s["accepted_action"],"phase":"PREEXISTING_ACCEPTED","at":s["final_time"]}];outcome="UNKNOWN"
    elif s["effect_state"]=="VERIFIED_BEFORE_STOP":
        events=[{"action":s["accepted_action"],"phase":"PREEXISTING_VERIFIED","at":s["final_time"]}];outcome="VERIFIED";verified=s["final_time"]
    elif s.get("release_required"):
        outcome="RELEASED"
    else:
        if p=="NAIVE_PROVISIONAL_EFFECT" and s.get("prefix_action"):
            events.append({"action":s["prefix_action"],"phase":"PROVISIONAL_CONSEQUENTIAL","at":0})
        if authorized:
            if p=="VERSION_BOUND_READ_ONLY_PREPARATION":
                used=(s.get("prep_action")==s["final_action"] and s["prep_epoch"]==s["final_epoch"] and s.get("prep_ready") is not None)
            start=max(s["final_time"],s["prep_ready"]) if used else s["final_time"]
            lookup=0 if used else c["final_lookup"]
            events.append({"action":s["final_action"],"phase":"FINAL_AUTHENTICATED_COMMIT","at":start+lookup})
            verified=start+lookup+c["dispatch"]+c["verify"];outcome="VERIFIED"
        else:outcome="NO_EFFECT"
    return {"scenario":s["id"],"policy":p,"final_action":s.get("final_action") if authorized else None,
            "events":events,"outcome":outcome,"verified_at_ms":verified,"prep_used":used,
            "release_preserved":bool(s.get("release_required")),"input_authorized":False}

def audit(raw,f):
    e=[]
    if raw.get("fixture_sha256")!=hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest():e.append("fixture digest mismatch")
    if raw.get("candidate_sha256")!=hashlib.sha256((HERE/"candidate.py").read_bytes()).hexdigest():e.append("candidate digest mismatch")
    expected=[oracle(s,p,f["costs_ms"]) for s in f["scenarios"] for p in f["policies"]]
    if raw.get("rows")!=expected:e.append("candidate trace differs from independent event replay")
    for r in raw.get("rows",[]):
        if any(ev["phase"]=="PROVISIONAL_CONSEQUENTIAL" for ev in r.get("events",[])) and r["policy"]!="NAIVE_PROVISIONAL_EFFECT":e.append("safe arm emitted provisional consequence")
        if r.get("policy")=="VERSION_BOUND_READ_ONLY_PREPARATION" and r.get("scenario")=="stale_completion_after_revision" and r.get("prep_used"):e.append("stale epoch completion revived")
        if r.get("scenario")=="urgent_physical_release" and not r.get("release_preserved"):e.append("urgent release lost")
        if r.get("input_authorized") is not False:e.append("simulator claims input authority")
    return e

def mutations(raw):
    cases={}
    def edit(name,pred,changes):
        v=copy.deepcopy(raw);next(x for x in v["rows"] if pred(x)).update(changes);cases[name]=v
    edit("reuse_old_epoch",lambda r:r["scenario"]=="stale_completion_after_revision" and r["policy"]=="VERSION_BOUND_READ_ONLY_PREPARATION",{"prep_used":True})
    edit("accept_provisional_as_final",lambda r:r["scenario"]=="mid_utterance_negation" and r["policy"]=="VERSION_BOUND_READ_ONLY_PREPARATION",{"events":[{"action":"SEND_A","phase":"FINAL_AUTHENTICATED_COMMIT","at":0}],"outcome":"VERIFIED"})
    edit("merge_speakers",lambda r:r["scenario"]=="two_speakers_overlap" and r["policy"]=="FINAL_ONLY",{"final_action":"SEND_A","events":[{"action":"SEND_A","phase":"FINAL_AUTHENTICATED_COMMIT","at":0}],"outcome":"VERIFIED"})
    edit("treat_stop_as_undo",lambda r:r["scenario"]=="stop_after_accepted_unknown_effect" and r["policy"]=="FINAL_ONLY",{"outcome":"NO_EFFECT","events":[]})
    return cases

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--raw",required=True,type=Path);ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
    f=json.loads((HERE/"fixture.json").read_text(encoding="utf-8"));raw=json.loads(a.raw.read_text(encoding="utf-8"));errors=audit(raw,f);controls={}
    for n,v in mutations(raw).items():
        e=audit(v,f);controls[n]={"rejected":bool(e),"errors":len(e)}
        if not e:errors.append("mutation accepted: "+n)
    rows=raw.get("rows",[]);by={(r["scenario"],r["policy"]):r for r in rows}
    saved=by[("stable_request","FINAL_ONLY")]["verified_at_ms"]-by[("stable_request","VERSION_BOUND_READ_ONLY_PREPARATION")]["verified_at_ms"]
    unsafe=sum(any(ev["phase"]=="PROVISIONAL_CONSEQUENTIAL" for ev in r["events"]) for r in rows if r["policy"]=="NAIVE_PROVISIONAL_EFFECT")
    mismatches=0
    for scenario in f["scenarios"]:
        final=by[(scenario["id"],"FINAL_ONLY")];versioned=by[(scenario["id"],"VERSION_BOUND_READ_ONLY_PREPARATION")]
        if final["outcome"]!=versioned["outcome"] or [e["action"] for e in final["events"]]!=[e["action"] for e in versioned["events"]]:
            mismatches+=1
    if saved<=0:errors.append("stable-turn preparation did not reduce declared latency")
    if mismatches:errors.append("version-bound effects differ from final-only contract")
    result={"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD","rows_reconstructed":len(rows),
            "stable_saved_ms":saved,"naive_provisional_scenarios_with_consequential_events":unsafe,
            "version_bound_outcome_mismatches_final_only":mismatches,
            "version_bound_wrong_or_duplicate_effects":sum(1 for r in rows if r["policy"]=="VERSION_BOUND_READ_ONLY_PREPARATION" and (len(r["events"])>1 or any(e["phase"]=="PROVISIONAL_CONSEQUENTIAL" for e in r["events"]))),
            "mutations":controls,"errors":errors,"scope":"finite scripted speech-revision event table; no ASR, GUI or human claim"}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,sort_keys=True));raise SystemExit(0 if not errors else 1)
if __name__=="__main__":main()

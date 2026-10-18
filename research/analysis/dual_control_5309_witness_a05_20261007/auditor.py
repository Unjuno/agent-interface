"""Independent raw-only exhaustive checker for A04; does not import candidate.py."""
import json
from pathlib import Path


ARMS = {"TASK_ONLY", "GENERIC_IG", "WITNESS_AWARE", "FAIL_CLOSED"}


def expected_selected(f, scenario, arm):
    actions=f["actions"]["generic_ig"]
    control=next((x for x in f["controls"] if x["id"]==scenario),{})
    ranked=[]
    for action in actions:
        score=f["model"]["predicted_information_gain_bits"][action]
        if arm=="WITNESS_AWARE" and not control.get("witness_already_available",False):
            score += 0.01 if f["model"]["predicted_witness_survival"][action] else 0.0
        ranked.append((score,action))
    return min(ranked,key=lambda item:(-item[0],item[1]))[1]


def expected_decision(f, scenario, state, arm):
    if scenario == "no-safe-path" or arm == "FAIL_CLOSED":
        return "UNKNOWN"
    if arm == "TASK_ONLY":
        return "UNKNOWN_TASK_TARGET"
    if scenario == "urgent-stop":
        return "STOP_AND_RELEASE"
    selected = expected_selected(f,scenario,arm)
    record = dict(f["realized"][selected])
    record.update(f.get("scenario_overrides",{}).get(scenario,{}).get(selected,{}))
    if scenario == "stale-receipt":
        return "UNKNOWN"
    if scenario == "misspecified-model" and f["model"]["predicted_observation"][selected] == "effect-witness" and record["payload_type"] != "state-plus-effect":
        return "UNKNOWN_MODEL_MISMATCH"
    if not (f["controls"][0]["witness_already_available"] if scenario == "witness-irrelevant" else record["witness_survives"]):
        return "UNKNOWN_EFFECT_WITNESS_LOST"
    if scenario == "duplicate-receipt":
        # Duplicate identity is consumed once; a single valid readback remains.
        pass
    return "COMPLETE"


def audit(f, raw):
    expected_scenarios={"primary","witness-irrelevant","no-safe-path","stale-receipt",
                        "duplicate-receipt","urgent-stop","misspecified-model"}
    rows=raw.get("rows")
    if type(rows) is not list or len(rows)!=len(expected_scenarios)*len(f["states"])*len(ARMS):
        raise ValueError("row coverage mismatch")
    seen=set(); errors=[]; decisions={}
    for row in rows:
        key=(row.get("scenario"),row.get("state"),row.get("arm"))
        if key in seen: errors.append("duplicate-row")
        seen.add(key)
        scenario,state,arm=key
        if scenario not in expected_scenarios or state not in f["states"] or arm not in ARMS:
            errors.append("unknown-row")
            continue
        want=expected_decision(f,scenario,state,arm)
        if row.get("decision")!=want: errors.append(f"decision:{key}")
        expected_set=[] if arm in {"TASK_ONLY","FAIL_CLOSED"} or scenario=="no-safe-path" else f["actions"]["generic_ig"]
        if row.get("admitted_action_set")!=expected_set: errors.append(f"action-set:{key}")
        if row.get("completed") is not (want=="COMPLETE"): errors.append(f"completion:{key}")
        if row.get("authority_grants")!=0: errors.append(f"authority:{key}")
        if want=="COMPLETE":
            witness=[e for e in row["trace"] if e.get("event")=="independent-readback"]
            commits=[e for e in row["trace"] if e.get("event")=="commit"]
            if len(witness)!=1 or len(commits)!=1 or witness[0].get("status")!="verified":
                errors.append(f"missing-independent-witness:{key}")
            selected=[e["action"] for e in row["trace"] if e.get("event")=="task-action"]
            if len(selected)!=1 or selected[0] not in f["realized"]:
                errors.append(f"selected-action:{key}")
        else:
            if any(e.get("event")=="commit" for e in row.get("trace",[])):
                errors.append(f"commit-after-noncomplete:{key}")
        if scenario=="duplicate-receipt" and arm in {"GENERIC_IG","WITNESS_AWARE"}:
            ids=[e["event_id"] for e in row["trace"] if e.get("event")=="duplicate-receipt"]
            if len(ids)!=2 or len(set(ids))!=1: errors.append(f"duplicate-control:{key}")
            if sum(e.get("event")=="receipt-consumed" for e in row["trace"])!=1:
                errors.append(f"duplicate-consumption:{key}")
        if arm in {"GENERIC_IG","WITNESS_AWARE"} and scenario!="no-safe-path":
            selected=[e["action"] for e in row["trace"] if e.get("event")=="task-action"]
            if selected != [expected_selected(f,scenario,arm)]: errors.append(f"ranked-choice:{key}")
        decisions[str(key)]=row.get("decision")
    if len(seen)!=len(expected_scenarios)*len(f["states"])*len(ARMS): errors.append("missing-row")
    if decisions.get(str(("primary","hidden-a","GENERIC_IG")))!="UNKNOWN_EFFECT_WITNESS_LOST":
        errors.append("generic-counterexample-missing")
    if decisions.get(str(("primary","hidden-a","WITNESS_AWARE")))!="COMPLETE":
        errors.append("witness-aware-route-missing")
    if errors: raise ValueError(";".join(errors))
    return {"status":"PASS_WITNESS_BOUNDARY_SCOPED","rows":len(rows),"errors":[],
            "primary_generic":"UNKNOWN_EFFECT_WITNESS_LOST","primary_witness_aware":"COMPLETE",
            "authority_grants":0}


if __name__ == "__main__":
    root=Path(__file__).resolve().parent
    from hashlib import sha256
    from datetime import datetime, timezone
    raw_path=root/"candidate-raw.json"
    result=audit(json.loads((root/"fixture.json").read_text()),json.loads(raw_path.read_text()))
    result.update({"utc":datetime.now(timezone.utc).isoformat(),"candidate_raw_sha256":sha256(raw_path.read_bytes()).hexdigest()})
    with (root/"audit.json").open("x",encoding="utf-8") as stream:
        json.dump(result,stream,sort_keys=True,separators=(",",":"));stream.write("\n")
    print(json.dumps({"status":result["status"],"audit_sha256":sha256((root/"audit.json").read_bytes()).hexdigest()},sort_keys=True,separators=(",",":")))

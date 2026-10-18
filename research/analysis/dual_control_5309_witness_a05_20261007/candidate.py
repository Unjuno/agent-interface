"""Finite A04 candidate: model-based action ranking, never an authority source."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ARMS = ("TASK_ONLY", "GENERIC_IG", "WITNESS_AWARE", "FAIL_CLOSED")


def simulate(fixture, scenario, state, arm):
    actions = fixture["actions"]
    truth = fixture["truth"][state]
    realized = fixture["realized"]
    trace = []
    authority_grants = 0
    control = fixture["controls_by_id"].get(scenario,{})
    if scenario == "no-safe-path":
        return {"scenario":scenario,"state":state,"arm":arm,"trace":[],"completed":False,
                "admitted_action_set":[],"witness_preserved":False,"authority_grants":0,"decision":"UNKNOWN"}
    if arm == "FAIL_CLOSED":
        return {"scenario":scenario,"state":state,"arm":arm,"trace":[],"completed":False,
                "admitted_action_set":[],"witness_preserved":True,"authority_grants":0,"decision":"UNKNOWN"}
    if arm == "TASK_ONLY":
        trace.append({"event":"task-proposal","actions":actions["task_only"]})
        return {"scenario":scenario,"state":state,"arm":arm,"trace":trace,"completed":False,
                "admitted_action_set":[],"witness_preserved":True,"authority_grants":authority_grants,"decision":"UNKNOWN_TASK_TARGET"}
    ig = fixture["model"]["predicted_information_gain_bits"]
    candidates = actions["generic_ig"]
    ranked = []
    for action in candidates:
        score = ig[action]
        if arm == "WITNESS_AWARE" and not control.get("witness_already_available",False):
            score += 0.01 if fixture["model"]["predicted_witness_survival"][action] else 0.0
        ranked.append((score, action))
    selected = min(ranked, key=lambda x:(-x[0],x[1]))[1]
    row = realized[selected]
    row = dict(row)
    row.update(fixture.get("scenario_overrides",{}).get(scenario,{}).get(selected,{}))
    admitted = list(candidates)
    trace.append({"event":"task-action","action":selected,"admissible":True,"model_ig_bits":ig[selected]})
    trace.append({"event":"receipt","receipt_type":fixture["model"]["predicted_observation"][selected],"fresh":row["fresh"] and scenario!="stale-receipt"})
    fresh = row["fresh"] and scenario != "stale-receipt"
    duplicate = scenario == "duplicate-receipt"
    observed = fixture["receipt_symbols"][state] if fresh else None
    if duplicate:
        trace.append({"event":"duplicate-receipt","event_id":"r1"})
        trace.append({"event":"duplicate-receipt","event_id":"r1"})
        trace.append({"event":"receipt-consumed","event_id":"r1","count":1})
    if scenario == "urgent-stop":
        trace.append({"event":"urgent-stop","release_verified":True})
        return {"scenario":scenario,"state":state,"arm":arm,"trace":trace,"completed":False,
                "admitted_action_set":admitted,"witness_preserved":row["witness_survives"],"authority_grants":authority_grants,
                "decision":"STOP_AND_RELEASE"}
    if not fresh or not observed:
        return {"scenario":scenario,"state":state,"arm":arm,"trace":trace,"completed":False,
                "admitted_action_set":admitted,"witness_preserved":row["witness_survives"],"authority_grants":authority_grants,"decision":"UNKNOWN"}
    model_observation = fixture["model"]["predicted_observation"][selected]
    observed_effect_witness = model_observation == "effect-witness" and row["payload_type"] == "state-plus-effect"
    witness_available = control.get("witness_already_available",False) or observed_effect_witness
    if scenario == "misspecified-model" and model_observation == "effect-witness" and row["payload_type"] != "state-plus-effect":
        return {"scenario":scenario,"state":state,"arm":arm,"trace":trace,"completed":False,
                "admitted_action_set":admitted,"witness_preserved":row["witness_survives"],"authority_grants":authority_grants,"decision":"UNKNOWN_MODEL_MISMATCH"}
    if not witness_available:
        return {"scenario":scenario,"state":state,"arm":arm,"trace":trace,"completed":False,
                "admitted_action_set":admitted,"witness_preserved":False,"authority_grants":authority_grants,"decision":"UNKNOWN_EFFECT_WITNESS_LOST"}
    commit = truth["correct_commit"]
    trace.append({"event":"independent-readback","effect_id":truth["effect_witness"],"status":"verified"})
    trace.append({"event":"commit","action":commit,"admissible":True})
    return {"scenario":scenario,"state":state,"arm":arm,"trace":trace,"admitted_action_set":admitted,"completed":True,
            "witness_preserved":True,"authority_grants":authority_grants,"decision":"COMPLETE"}


def run(fixture):
    fixture = dict(fixture)
    fixture["controls_by_id"] = {row["id"]:row for row in fixture["controls"]}
    rows=[]
    scenarios=["primary","witness-irrelevant","no-safe-path","stale-receipt",
               "duplicate-receipt","urgent-stop","misspecified-model"]
    for scenario in scenarios:
        for state in fixture["states"]:
            for arm in ARMS:
                rows.append(simulate(fixture,scenario,state,arm))
    return {"allocation":fixture["allocation"],"rows":rows}


if __name__ == "__main__":
    from hashlib import sha256
    from datetime import datetime, timezone
    out = ROOT/"candidate-raw.json"
    with out.open("x", encoding="utf-8") as stream:
        json.dump(run(json.loads((ROOT/"fixture.json").read_text())),stream,sort_keys=True,separators=(",",":"))
        stream.write("\n")
    print(json.dumps({"status":"CANDIDATE_COMPLETE","utc":datetime.now(timezone.utc).isoformat(),
                      "raw_sha256":sha256(out.read_bytes()).hexdigest()},sort_keys=True,separators=(",",":")))

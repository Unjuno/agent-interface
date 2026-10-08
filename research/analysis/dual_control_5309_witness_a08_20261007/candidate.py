"""Candidate policy: accepts only candidate-input bytes and observed receipts."""
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path


ARMS = ("TASK_ONLY", "GENERIC_IG", "WITNESS_AWARE", "FAIL_CLOSED")


def select_action(case, model, arm):
    ranked = []
    for action in case["admissible_actions"]:
        score = model["predicted_ig_bits"][action]
        if arm == "WITNESS_AWARE":
            score += 0.01 if model["predicted_witness_survival"][action] else 0.0
        ranked.append((score, action))
    return min(ranked, key=lambda item: (-item[0], item[1]))[1]


def simulate(case, models, arm):
    trace = []
    row = {"case_id": case["case_id"], "scenario": case["scenario"], "arm": arm,
           "admitted_action_set": list(case["admissible_actions"]), "trace": trace,
           "completed": False, "authority_grants": 0}
    if arm == "FAIL_CLOSED":
        row["decision"] = "UNKNOWN"
        return row
    if arm == "TASK_ONLY":
        trace.append({"event": "task-proposal"})
        row["decision"] = "UNKNOWN_TASK_TARGET"
        return row
    if not case["admissible_actions"]:
        row["decision"] = "UNKNOWN"
        return row

    model = models["witness_aware"]
    action = select_action(case, model if arm == "WITNESS_AWARE" else models["generic_ig"], arm)
    trace.append({"event": "task-action", "action": action, "admissible": True})
    if case.get("urgent_stop"):
        trace.append({"event": "urgent-stop", "release_verified": case.get("release_verified", False)})
        row["decision"] = "STOP_AND_RELEASE" if case.get("release_verified") else "UNKNOWN_RELEASE"
        return row

    outcome = case["action_effect_receipts"][action]
    trace.append({"event": "state-receipt", "symbol": case["receipt_symbol"], "fresh": case["receipt_fresh"]})
    if case.get("duplicate_event_ids"):
        for event_id in case["duplicate_event_ids"]:
            trace.append({"event": "duplicate-receipt", "event_id": event_id})
        trace.append({"event": "receipt-consumed", "event_id": case["duplicate_event_ids"][0], "count": 1})
    if not case["receipt_fresh"]:
        row["decision"] = "UNKNOWN"
        return row

    proof = case.get("preexisting_effect_receipt") or outcome
    expected_survival = models["witness_aware"]["predicted_witness_survival"][action]
    if proof is None:
        row["decision"] = "UNKNOWN_MODEL_MISMATCH" if expected_survival else "UNKNOWN_EFFECT_WITNESS_LOST"
        return row

    commit = models["receipt_to_task_action"].get(case["receipt_symbol"])
    if commit is None:
        row["decision"] = "UNKNOWN"
        return row
    trace.append({"event": "independent-readback", "receipt": proof, "status": "verified"})
    trace.append({"event": "commit", "action": commit, "admissible": True})
    row["completed"] = True
    row["decision"] = "COMPLETE"
    return row


def run(candidate_input):
    rows = []
    for case in candidate_input["cases"]:
        for arm in ARMS:
            rows.append(simulate(case, candidate_input["models"], arm))
    return {"allocation": candidate_input["allocation"], "rows": rows}


if __name__ == "__main__":
    source = Path("/input/candidate-input.json").read_bytes()
    result = run(json.loads(source))
    output = Path("/out/candidate-raw.json")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "utc": datetime.now(timezone.utc).isoformat(),
                      "input_sha256": sha256(source).hexdigest(),
                      "raw_sha256": sha256(output.read_bytes()).hexdigest()}, sort_keys=True, separators=(",", ":")))

"""Raw-only oracle checker; loaded only in the auditor container."""
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path


ARMS = {"TASK_ONLY", "GENERIC_IG", "WITNESS_AWARE", "FAIL_CLOSED"}


def expected_action(case, models, arm):
    candidates = []
    model = models["witness_aware"] if arm == "WITNESS_AWARE" else models["generic_ig"]
    for action in case["admissible_actions"]:
        score = model["predicted_ig_bits"][action]
        if arm == "WITNESS_AWARE":
            score += 0.01 if model["predicted_witness_survival"][action] else 0.0
        candidates.append((score, action))
    return min(candidates, key=lambda item: (-item[0], item[1]))[1] if candidates else None


def expected_decision(case, models, arm):
    if arm == "FAIL_CLOSED":
        return "UNKNOWN"
    if arm == "TASK_ONLY":
        return "UNKNOWN_TASK_TARGET"
    if not case["admissible_actions"]:
        return "UNKNOWN"
    if case.get("urgent_stop"):
        return "STOP_AND_RELEASE" if case.get("release_verified") else "UNKNOWN_RELEASE"
    if not case["receipt_fresh"]:
        return "UNKNOWN"
    action = expected_action(case, models, arm)
    proof = case.get("preexisting_effect_receipt") or case["action_effect_receipts"][action]
    if proof is None:
        predicted = models["witness_aware"]["predicted_witness_survival"][action]
        return "UNKNOWN_MODEL_MISMATCH" if predicted else "UNKNOWN_EFFECT_WITNESS_LOST"
    return "COMPLETE" if models["receipt_to_task_action"].get(case["receipt_symbol"]) else "UNKNOWN"


def audit(candidate_input, oracle, raw):
    cases = {case["case_id"]: case for case in candidate_input["cases"]}
    truth = oracle["truth_by_case_id"]
    errors = []
    rows = raw.get("rows")
    if type(rows) is not list or len(rows) != len(cases) * len(ARMS):
        raise ValueError("row coverage mismatch")
    seen = set()
    decisions = {}
    for row in rows:
        key = (row.get("case_id"), row.get("arm"))
        if key in seen:
            errors.append("duplicate-row")
        seen.add(key)
        case_id, arm = key
        if case_id not in cases or arm not in ARMS:
            errors.append("unknown-row")
            continue
        case = cases[case_id]
        expected = expected_decision(case, candidate_input["models"], arm)
        if row.get("scenario") != case["scenario"]:
            errors.append(f"scenario:{key}")
        if row.get("admitted_action_set") != case["admissible_actions"]:
            errors.append(f"admitted-set:{key}")
        if row.get("decision") != expected:
            errors.append(f"decision:{key}")
        if row.get("completed") is not (expected == "COMPLETE"):
            errors.append(f"completion:{key}")
        if row.get("authority_grants") != 0:
            errors.append(f"authority:{key}")

        task_actions = [event.get("action") for event in row.get("trace", []) if event.get("event") == "task-action"]
        if arm in {"GENERIC_IG", "WITNESS_AWARE"} and case["admissible_actions"]:
            if task_actions != [expected_action(case, candidate_input["models"], arm)]:
                errors.append(f"rank-choice:{key}")
        elif task_actions:
            errors.append(f"unexpected-action:{key}")

        commits = [event.get("action") for event in row.get("trace", []) if event.get("event") == "commit"]
        readbacks = [event.get("receipt") for event in row.get("trace", []) if event.get("event") == "independent-readback"]
        if expected == "COMPLETE":
            if commits != [truth[case_id]["correct_commit"]]:
                errors.append(f"wrong-commit:{key}")
            if len(readbacks) != 1 or readbacks[0] != truth[case_id]["effect_receipt"]:
                errors.append(f"effect-proof:{key}")
            if len(task_actions) != 1:
                errors.append(f"action-count:{key}")
        elif commits or readbacks:
            errors.append(f"commit-or-proof-after-noncomplete:{key}")

        if case["scenario"] == "urgent-stop" and arm in {"GENERIC_IG", "WITNESS_AWARE"}:
            if not any(event.get("event") == "urgent-stop" and event.get("release_verified") for event in row["trace"]):
                errors.append(f"stop-release:{key}")
        if case["scenario"] == "duplicate-receipt" and arm in {"GENERIC_IG", "WITNESS_AWARE"}:
            duplicates = [event.get("event_id") for event in row["trace"] if event.get("event") == "duplicate-receipt"]
            consumed = [event for event in row["trace"] if event.get("event") == "receipt-consumed"]
            if len(duplicates) != 2 or len(set(duplicates)) != 1 or len(consumed) != 1 or consumed[0].get("count") != 1:
                errors.append(f"dedup:{key}")
        decisions[str(key)] = row.get("decision")

    if len(seen) != len(cases) * len(ARMS):
        errors.append("missing-row")
    primary_generic = next((row for row in rows if row.get("scenario") == "primary" and row.get("arm") == "GENERIC_IG"), {})
    primary_aware = next((row for row in rows if row.get("scenario") == "primary" and row.get("arm") == "WITNESS_AWARE"), {})
    if primary_generic.get("decision") != "UNKNOWN_EFFECT_WITNESS_LOST":
        errors.append("primary-generic-counterexample-missing")
    if primary_aware.get("decision") != "COMPLETE":
        errors.append("primary-aware-completion-missing")
    if errors:
        raise ValueError(";".join(errors))
    return {"status": "PASS_WITNESS_BOUNDARY_SCOPED", "rows": len(rows), "errors": [],
            "primary_generic": primary_generic["decision"], "primary_witness_aware": primary_aware["decision"],
            "authority_grants": 0}


if __name__ == "__main__":
    candidate_input = Path("/input/candidate-input.json").read_bytes()
    oracle_bytes = Path("/input/oracle.json").read_bytes()
    raw_bytes = Path("/input/candidate-raw.json").read_bytes()
    result = audit(json.loads(candidate_input), json.loads(oracle_bytes), json.loads(raw_bytes))
    result.update({"utc": datetime.now(timezone.utc).isoformat(),
                   "candidate_input_sha256": sha256(candidate_input).hexdigest(),
                   "oracle_sha256": sha256(oracle_bytes).hexdigest(),
                   "candidate_raw_sha256": sha256(raw_bytes).hexdigest()})
    output = Path("/out/audit.json")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"status": result["status"], "audit_sha256": sha256(output.read_bytes()).hexdigest()},
                     sort_keys=True, separators=(",", ":")))

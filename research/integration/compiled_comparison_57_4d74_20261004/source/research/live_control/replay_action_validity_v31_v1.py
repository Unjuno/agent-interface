"""Counterfactual, model-free action-validity replay over retained v31 evidence."""
import argparse
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DOOM = REPO / "research/doom"
sys.path.insert(0, str(HERE))
from action_validity_admission_v1 import (
    CONTRACT_FORMAT, SNAPSHOT_FORMAT, action_fingerprint,
    evaluate_action_validity)


TRACE = DOOM / "results/map01-soft-context-v31-live-01/report.json"


def _current_health(decision, source_signal):
    event = decision.get("cover_validity_latest_soft_event")
    fresh_sequence = decision["fresh_sequence_at_plan"]
    if event is not None and event["sequence"] <= fresh_sequence:
        return event["signal"]["value"]
    return source_signal["value"]


def run():
    report = json.loads(TRACE.read_text())
    rows = []
    for decision in report["decisions"]:
        if decision.get("plan_terminal") != "completed":
            continue
        source_signal = decision["cover_validity_admission"]["source_signal"]
        commands = decision["action"]["commands"]
        accepted_ns = decision["execution_trace"][0]["accepted_ns"]
        current_capture_ns = accepted_ns - decision["fresh_observation_to_plan_accept_ns"]
        current_health = _current_health(decision, source_signal)
        source = {"sequence": source_signal["sequence"],
                  "capture_ns": source_signal["capture_ns"],
                  "binding": source_signal["binding"],
                  "signals": {"health": {"status": "observed",
                                          "value": source_signal["value"]}}}
        contract = {"format": CONTRACT_FORMAT,
                    "action_fingerprint": action_fingerprint(commands),
                    "source": source, "max_current_age_ms": 500,
                    "predicates": [
                        {"signal_id": "health", "operator": "minimum", "value": 45},
                        {"signal_id": "health", "operator": "max_decrease_from_source",
                         "value": 8}]}
        snapshot = {"format": SNAPSHOT_FORMAT,
                    "sequence": decision["fresh_sequence_at_plan"],
                    "capture_ns": current_capture_ns,
                    "binding": source_signal["binding"],
                    "signals": {"health": {"status": "observed",
                                            "value": current_health}}}
        result = evaluate_action_validity(commands, contract, snapshot, accepted_ns)
        initial_contract = json.loads(json.dumps(contract))
        initial_contract["max_current_age_ms"] = 250
        initial_result = evaluate_action_validity(
            commands, initial_contract, snapshot, accepted_ns)
        rows.append({"iteration": decision["iteration"], "commands": commands,
                     "source_health": source_signal["value"],
                     "current_health": current_health,
                     "current_age_ns_at_historical_acceptance":
                         accepted_ns - current_capture_ns,
                     "strict_unchanged_baseline":
                         "PASS" if current_health == source_signal["value"] else "REJECT",
                     "initial_250ms_status": initial_result["status"],
                     "candidate_status": result["status"],
                     "candidate_result": result})
    assert len(rows) == 5
    assert sum(row["strict_unchanged_baseline"] == "REJECT" for row in rows) == 4
    assert [row["initial_250ms_status"] for row in rows].count("REJECTED_STALE") == 1
    assert all(row["candidate_status"] == "VALID_CURRENT" for row in rows)

    # These are construction controls, not claims about states that occurred live.
    base = rows[2]["candidate_result"]
    contract = base["contract"]
    snapshot = base["snapshot"]
    breach = json.loads(json.dumps(snapshot))
    breach["signals"]["health"]["value"] = contract["source"]["signals"]["health"]["value"] - 9
    breach_result = evaluate_action_validity(
        rows[2]["commands"], contract, breach, base["controller_decided_ns"])
    required_enemy = json.loads(json.dumps(contract))
    required_enemy["source"]["signals"]["enemy_visible"] = {
        "status": "observed", "value": True}
    required_enemy["predicates"].append({
        "signal_id": "enemy_visible", "operator": "equals", "value": True})
    unknown_enemy = json.loads(json.dumps(snapshot))
    unknown_enemy["signals"]["enemy_visible"] = {"status": "unknown", "value": None}
    unknown_result = evaluate_action_validity(
        rows[2]["commands"], required_enemy, unknown_enemy,
        base["controller_decided_ns"])
    assert breach_result["status"] == "REJECTED_PREDICATE"
    assert unknown_result["status"] == "REJECTED_SIGNAL_UNKNOWN"
    return {
        "schema": "retained-v31-action-validity-replay-v1",
        "passed": True,
        "historical_rows": rows,
        "historical_completed_plans": len(rows),
        "strict_unchanged_rejections": 4,
        "initial_250ms_candidate_rejections": 1,
        "initial_250ms_failure": "retained iteration 2 current observation age is 333.611475ms at historical acceptance",
        "bounded_health_candidate_passes": 5,
        "construction_controls": {
            "health_beyond_envelope": breach_result,
            "required_enemy_signal_unknown": unknown_result},
        "model_calls": 0,
        "input_operations": 0,
        "interpretation": "A typed bounded-health predicate avoids four counterfactual unchanged-state rejections while rejecting a larger decrease; a required but unavailable enemy signal rejects instead of being silently ignored.",
        "limits": "Contracts are synthetic construction inputs chosen before this replay implementation, not outputs authored in the retained live run. Health-only validity does not establish action usefulness, enemy persistence, aim, safety, latency improvement, or gameplay gain.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "audit.json").write_bytes(
        (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print(json.dumps({"passed": result["passed"],
                      "strict_unchanged_rejections": result["strict_unchanged_rejections"],
                      "bounded_health_candidate_passes": result["bounded_health_candidate_passes"],
                      "output": str(args.out / "audit.json")}, separators=(",", ":")))


if __name__ == "__main__":
    main()

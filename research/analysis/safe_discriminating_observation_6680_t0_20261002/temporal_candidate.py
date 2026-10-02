"""Candidate policy simulator for the temporal #6680 construction model."""

import json
import sys
from pathlib import Path


def predict_position(fixture, tick):
    model = fixture["predictor"]
    return model["intercept"] + model["velocity"] * tick


def predictor_matches_frozen_trajectory(fixture):
    return all(point["position"] == predict_position(fixture, point["tick"]) for point in fixture["target_trajectory"])


def release_confirmed(case):
    lease = case["lease"]
    if lease["held_input"] is None:
        return True
    receipt = lease.get("release_receipt")
    return bool(
        receipt
        and receipt.get("lease_id") == lease["id"]
        and receipt.get("tick") == lease["release_requested_tick"]
    )


def recovery_for_probe(fixture, observation):
    if not observation.get("supported", True):
        return None
    age = observation["received_tick"] - observation["source_tick"]
    if age < 0:
        return None
    residual = abs(observation["position"] - predict_position(fixture, observation["received_tick"]))
    signature = {"source_age": age, "residual": residual}
    compatible = [
        item["recovery"] for item in fixture["signature_recoveries"]
        if item["source_age"] == age and item["residual"] == residual
    ]
    return compatible[0] if len(compatible) == 1 else None


def choose(fixture, case, policy):
    lease = case["lease"]
    released = release_confirmed(case)
    alarm = case["pre_probe_observation"]
    alarm_residual = abs(alarm["position"] - predict_position(fixture, alarm["received_tick"]))
    alarm_active = alarm_residual >= fixture["alarm_threshold"]
    alarm_time_valid = alarm["source_tick"] <= alarm["received_tick"] <= fixture["probe"]["tick"]
    if not predictor_matches_frozen_trajectory(fixture) or not released or not alarm_active or not alarm_time_valid:
        return "yield", 0, alarm_residual, None, None
    if policy == "always_reobserve":
        if fixture["max_probe_observations"] >= 1:
            return "reobserve", 1, alarm_residual, None, None
        return "yield", 0, alarm_residual, None, None
    if policy == "always_reset":
        return "reset", 0, alarm_residual, None, None
    if policy == "immediate_yield":
        return "yield", 0, alarm_residual, None, None
    if policy != "bounded_diagnose":
        raise ValueError(f"unknown policy: {policy}")
    probe = fixture["probe"]
    observation = case["probe_observation"]
    admissible = (
        fixture["max_probe_observations"] >= 1
        and probe["admissible"] and not probe["effectful"] and not probe["extends_lease"]
        and observation["admissible"]
        and observation.get("supported", True)
        and observation["received_tick"] == probe["tick"]
        and observation["source_tick"] <= observation["received_tick"]
        and lease["release_receipt"]["tick"] <= observation["received_tick"]
    )
    if not admissible:
        return "yield", 0, alarm_residual, None, None
    age = observation["received_tick"] - observation["source_tick"]
    residual = abs(observation["position"] - predict_position(fixture, observation["received_tick"]))
    signature = {"source_age": age, "residual": residual}
    action = recovery_for_probe(fixture, observation) or "yield"
    return action, 1, alarm_residual, age, residual


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        for policy in fixture["policies"]:
            action, observations, alarm_residual, age, residual = choose(fixture, case, policy)
            receipt = case["lease"].get("release_receipt")
            rows.append({
                "case_id": case["id"],
                "policy": policy,
                "action": action,
                "diagnostic_observations": observations,
                "alarm_residual": alarm_residual,
                "alarm_source_age": case["pre_probe_observation"]["received_tick"] - case["pre_probe_observation"]["source_tick"] if case["pre_probe_observation"]["source_tick"] <= case["pre_probe_observation"]["received_tick"] else None,
                "release_lease_id": receipt.get("lease_id") if receipt else None,
                "release_receipt_tick": receipt.get("tick") if receipt else None,
                "probe_observation_tick": case["probe_observation"]["received_tick"] if observations else None,
                "probe_source_age": age,
                "probe_residual": residual,
            })
    return {"schema": "safe-discriminating-observation-6680-temporal-raw-v1", "rows": rows}


if __name__ == "__main__":
    base = Path(__file__).parent
    fixture = json.loads((base / "temporal_fixture.json").read_text())
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("temporal_candidate.raw.json")
    output.write_text(json.dumps(run(fixture), sort_keys=True, indent=2) + "\n")
    print(json.dumps({"rows": len(run(fixture)["rows"]), "output": str(output)}))

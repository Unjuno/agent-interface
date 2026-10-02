"""Independent event/decision/effect reconstruction for temporal #6680 raw."""

import json
import sys
from pathlib import Path


def _predict(fixture, tick):
    model = fixture["predictor"]
    return model["intercept"] + model["velocity"] * tick


def _predictor_matches_trajectory(fixture):
    return all(point["position"] == _predict(fixture, point["tick"]) for point in fixture["target_trajectory"])


def _expected_decision(fixture, case, policy):
    lease = case["lease"]
    receipt = lease.get("release_receipt")
    release_ok = lease["held_input"] is None or bool(
        receipt
        and receipt.get("lease_id") == lease["id"]
        and receipt.get("tick") == lease["release_requested_tick"]
    )
    pre = case["pre_probe_observation"]
    alarm_residual = abs(pre["position"] - _predict(fixture, pre["received_tick"]))
    alarm_time_valid = pre["source_tick"] <= pre["received_tick"] <= fixture["probe"]["tick"]
    if not _predictor_matches_trajectory(fixture) or not release_ok or alarm_residual < fixture["alarm_threshold"] or not alarm_time_valid:
        return "yield", 0, alarm_residual, None, None
    if policy == "always_reobserve":
        if fixture["max_probe_observations"] >= 1:
            return "reobserve", 1, alarm_residual, None, None
        return "yield", 0, alarm_residual, None, None
    if policy == "always_reset":
        return "reset", 0, alarm_residual, None, None
    if policy == "immediate_yield":
        return "yield", 0, alarm_residual, None, None
    probe = fixture["probe"]
    observation = case["probe_observation"]
    probe_ok = (
        fixture["max_probe_observations"] >= 1
        and probe["admissible"] and not probe["effectful"] and not probe["extends_lease"]
        and observation["admissible"] and observation.get("supported", True)
        and observation["received_tick"] == probe["tick"]
        and observation["source_tick"] <= observation["received_tick"]
        and (lease["held_input"] is None or receipt["tick"] <= observation["received_tick"])
    )
    if not probe_ok:
        return "yield", 0, alarm_residual, None, None
    age = observation["received_tick"] - observation["source_tick"]
    residual = abs(observation["position"] - _predict(fixture, observation["received_tick"]))
    matches = [rule["recovery"] for rule in fixture["signature_recoveries"] if (rule["source_age"], rule["residual"]) == (age, residual)]
    return (matches[0] if len(matches) == 1 else "yield"), 1, alarm_residual, age, residual


def audit(raw, fixture, oracle):
    errors = []
    if raw.get("schema") != "safe-discriminating-observation-6680-temporal-raw-v1":
        errors.append("raw schema mismatch")
    got = raw.get("rows")
    expected = []
    for case in fixture["cases"]:
        for policy in fixture["policies"]:
            action, observations, alarm_residual, age, residual = _expected_decision(fixture, case, policy)
            receipt = case["lease"].get("release_receipt")
            expected.append({
                "case_id": case["id"], "policy": policy, "action": action,
                "diagnostic_observations": observations, "alarm_residual": alarm_residual,
                "alarm_source_age": case["pre_probe_observation"]["received_tick"] - case["pre_probe_observation"]["source_tick"] if case["pre_probe_observation"]["source_tick"] <= case["pre_probe_observation"]["received_tick"] else None,
                "release_lease_id": receipt.get("lease_id") if receipt else None,
                "release_receipt_tick": receipt.get("tick") if receipt else None,
                "probe_observation_tick": case["probe_observation"]["received_tick"] if observations else None,
                "probe_source_age": age, "probe_residual": residual,
            })
    if got != expected:
        errors.append("raw decisions or event-derived fields differ from independent reconstruction")
    if len(got or []) != len(fixture["cases"]) * len(fixture["policies"]):
        errors.append("world-policy coverage mismatch")
    cases_by_id = {item["id"]: item for item in fixture["cases"]}
    for row in got or []:
        if row.get("diagnostic_observations", 0) <= 0:
            continue
        case = cases_by_id.get(row.get("case_id"))
        if case is None:
            continue
        receipt = case["lease"].get("release_receipt")
        probe_tick = case["probe_observation"]["received_tick"]
        if not receipt or row.get("release_lease_id") != case["lease"]["id"] or row.get("release_receipt_tick") != receipt.get("tick") or receipt.get("tick") > probe_tick:
            errors.append("raw probe/recovery lacks a timely matching release receipt")

    effect_rows = []
    for row in expected:
        case = next(item for item in fixture["cases"] if item["id"] == row["case_id"])
        lease = case["lease"]
        receipt = lease.get("release_receipt")
        if row["diagnostic_observations"]:
            probe_tick = case["probe_observation"]["received_tick"]
            if not receipt or receipt.get("lease_id") != lease["id"] or receipt.get("tick") > probe_tick:
                errors.append("probe/recovery occurred before matching release receipt")
        truth = oracle["worlds"][row["case_id"]]
        effect = truth["effects"][row["action"]]
        correct = truth["correct_recovery"]
        effect_rows.append({
            "case_id": row["case_id"], "policy": row["policy"], "action": row["action"],
            "wrong_recovery": row["action"] in ("reobserve", "reset") and row["action"] != correct,
            "useful_effect": effect["useful"],
            "post_recovery_residual": effect["post_recovery_residual"],
            "repeated_residual": effect["post_recovery_residual"] is not None and effect["post_recovery_residual"] >= fixture["alarm_threshold"],
            "release_latency": None if not receipt else receipt["tick"] - lease["release_requested_tick"],
        })
    yield_latency = {r["case_id"]: r["release_latency"] for r in effect_rows if r["policy"] == "immediate_yield"}
    comparable_latencies = []
    for row in effect_rows:
        baseline = yield_latency.get(row["case_id"])
        if baseline is not None and row["release_latency"] is not None:
            comparable_latencies.append((row["release_latency"], baseline))
            if row["release_latency"] > baseline:
                errors.append("worst-case release latency exceeded immediate YIELD baseline")
    gates = [r for r in effect_rows if r["case_id"] in oracle["identifiable_case_ids"]]
    diagnose = [r for r in gates if r["policy"] == "bounded_diagnose"]
    fixed = {p: [r for r in gates if r["policy"] == p] for p in ("always_reobserve", "always_reset")}
    counts = {p: sum(r["wrong_recovery"] for r in rows) for p, rows in fixed.items()}
    diag_wrong = sum(r["wrong_recovery"] for r in diagnose)
    recurrence_counts = {p: sum(r["repeated_residual"] for r in rows) for p, rows in fixed.items()}
    diag_recurrences = sum(r["repeated_residual"] for r in diagnose)
    if any(r["action"] != oracle["worlds"][r["case_id"]]["correct_recovery"] for r in diagnose):
        errors.append("diagnostic policy failed an identifiable recovery case")
    if not all(diag_wrong < n for n in counts.values()):
        errors.append("diagnosis did not strictly reduce wrong recovery against both fixed arms")
    if not all(diag_recurrences < n for n in recurrence_counts.values()):
        errors.append("diagnosis did not strictly reduce post-recovery residual recurrence against both fixed arms")
    for row in expected:
        if row["policy"] == "bounded_diagnose" and row["case_id"] not in oracle["identifiable_case_ids"] and row["action"] != "yield":
            errors.append("diagnostic policy acted on unknown, ineligible, or unsupported evidence")
        if row["diagnostic_observations"] > fixture["max_probe_observations"]:
            errors.append("probe budget exceeded")
    return {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "rows": len(expected), "errors": errors, "effect_rows": effect_rows,
        "worst_case_release_latency": max((item[0] for item in comparable_latencies), default=None),
        "immediate_yield_worst_case_release_latency": max((item[1] for item in comparable_latencies), default=None),
        "identifiable_counts": {
            "bounded_diagnose_wrong_recoveries": diag_wrong,
            "bounded_diagnose_useful_effects": sum(r["useful_effect"] for r in diagnose),
            "bounded_diagnose_repeated_residuals": sum(r["repeated_residual"] for r in diagnose),
            "always_reobserve_wrong_recoveries": counts["always_reobserve"],
            "always_reset_wrong_recoveries": counts["always_reset"],
            "always_reobserve_repeated_residuals": recurrence_counts["always_reobserve"],
            "always_reset_repeated_residuals": recurrence_counts["always_reset"],
            "immediate_yield_wrong_recoveries": sum(r["wrong_recovery"] for r in gates if r["policy"] == "immediate_yield"),
            "immediate_yield_useful_effects": sum(r["useful_effect"] for r in gates if r["policy"] == "immediate_yield"),
        },
    }


if __name__ == "__main__":
    base = Path(__file__).parent
    raw = json.loads(Path(sys.argv[1]).read_text())
    result = audit(raw, json.loads((base / "temporal_fixture.json").read_text()), json.loads((base / "temporal_oracle.json").read_text()))
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(rendered)
    print(rendered, end="")
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)

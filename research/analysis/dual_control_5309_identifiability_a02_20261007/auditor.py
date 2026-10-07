#!/usr/bin/env python3
"""Independent finite pairwise oracle and raw-contract audit for #5309 A02."""
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def independent_entropy(probabilities):
    return -sum(float(p) * math.log(float(p), 2) for p in probabilities if p > 0)


def pairwise_separator(case, left, right):
    """Enumerate all common action sequences; compare left and right histories."""
    allowed_by_step = case["allowed_by_step"]
    observations = case["observations"]
    expiry = case["expiry_before_step"]
    for depth in range(1, len(allowed_by_step) + 1):
        for sequence in itertools.product(*allowed_by_step[:depth]):
            left_history = []
            right_history = []
            for step, action in enumerate(sequence):
                admitted = action in allowed_by_step[step] and (expiry is None or step < expiry)
                if not admitted:
                    continue
                left_history.append(observations[action][left])
                right_history.append(observations[action][right])
            if left_history and left_history != right_history:
                return {"separated": True, "sequence": list(sequence), "left_history": left_history, "right_history": right_history}
    return {"separated": False, "sequence": None, "left_history": None, "right_history": None}


def opportunity_accounting(fixture, truth, state):
    total = len(fixture["exogenous_opportunity_stream"])
    consumed = truth["actions"]["probe_mode"]["opportunity_cost_by_state"][state]
    return {"state": state, "counterfactual_preserved": total, "after_probe_mode": max(0, total - consumed), "displaced": min(total, consumed)}


def audit(raw, fixture, truth):
    errors = []
    if raw.get("allocation") != fixture["allocation"]:
        errors.append("allocation mismatch")
    expected_fixture_sha = hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest()
    if raw.get("fixture_sha256") != expected_fixture_sha:
        errors.append("fixture hash mismatch")
    claimed_sha = raw.get("raw_sha256")
    raw_without_sha = dict(raw)
    raw_without_sha.pop("raw_sha256", None)
    if claimed_sha != canonical_sha(raw_without_sha):
        errors.append("raw checksum mismatch")

    one = raw.get("generic_one_step", {})
    prior = fixture["prior"]
    before = independent_entropy(list(prior.values()))
    outcome_mass = {}
    mode_map = fixture["mode_observation"]
    for state, p in prior.items():
        obs = mode_map[state]
        outcome_mass[obs] = outcome_mass.get(obs, 0.0) + p
    expected_after = 0.0
    for obs, mass in outcome_mass.items():
        posterior = [p / mass for state, p in prior.items() if mode_map[state] == obs]
        expected_after += mass * independent_entropy(posterior)
    if one.get("proposal") != "probe_mode" or one.get("admitted") is not True or one.get("executed") != "probe_mode":
        errors.append("one-step proposal/admission/execution mismatch")
    if one.get("observation") is None:
        errors.append("one-step observation missing")
    if not math.isclose(one.get("entropy_before_bits", math.nan), before, abs_tol=1e-12):
        errors.append("initial entropy mismatch")
    if not math.isclose(one.get("expected_entropy_after_bits", math.nan), expected_after, abs_tol=1e-12):
        errors.append("posterior entropy mismatch")
    gain = before - expected_after
    if not math.isclose(one.get("information_gain_bits", math.nan), gain, abs_tol=1e-12) or not math.isclose(gain, 1.0, abs_tol=1e-12):
        errors.append("information gain mismatch")

    repeat = raw.get("repeated_benign_branch", {})
    events = repeat.get("events", [])
    if len(events) != fixture["repeat_count"]:
        errors.append("repeat event count mismatch")
    for event in events:
        if (event.get("proposal"), event.get("admitted"), event.get("executed"), event.get("observation")) != ("repeat", True, "repeat", "routine"):
            errors.append("repeat event contract mismatch")
        if event.get("task_progress") is not True:
            errors.append("benign-branch progress missing")
    if repeat.get("authority_granted") is not False or one.get("authority_granted") is not False or raw.get("authority_granted") is not False:
        errors.append("authority promoted")

    if raw.get("planned_probe_sequences") != fixture["planned_probe_sequences"]:
        errors.append("planned probe sequence mismatch")
    opportunity_stream = fixture["exogenous_opportunity_stream"]
    if raw.get("exogenous_opportunity_stream") != opportunity_stream:
        errors.append("exogenous opportunity stream changed")
    counterfactual = raw.get("no_action_counterfactual", {})
    if (counterfactual.get("executed"), counterfactual.get("observation"), counterfactual.get("opportunities_preserved")) != (None, None, len(opportunity_stream)):
        errors.append("no-action counterfactual mismatch")

    pair_results = []
    expected_by_scenario = {"mode_alias": False, "separator_available": True, "no_separator": False, "expiry_before_separator": False, "one_step_null": True}
    for scenario_id, expected in expected_by_scenario.items():
        case = truth["scenarios"][scenario_id]
        for left, right in case["relevant_pairs"]:
            separated = pairwise_separator(case, left, right)
            if separated["separated"] is not expected:
                errors.append(f"oracle expected separator mismatch: {scenario_id}:{left}:{right}")
            same_safe_commit = truth["safe_commit"][left] == truth["safe_commit"][right]
            gate = "UNKNOWN/YIELD" if not same_safe_commit and not separated["separated"] else ("PAIR_DISTINGUISHED" if separated["separated"] else "NO_DECISION_RELEVANT_ALIAS")
            if scenario_id in ("mode_alias", "no_separator", "expiry_before_separator") and gate != "UNKNOWN/YIELD":
                errors.append(f"non-identifiable pair not held: {scenario_id}:{left}:{right}")
            pair_results.append({"scenario": scenario_id, "pair": [left, right], "safe_commits_differ": not same_safe_commit, **separated, "gate": gate})

    expiry_case = truth["scenarios"]["expiry_before_separator"]
    expiry_step = expiry_case["expiry_before_step"]
    expired_proposal = raw["planned_probe_sequences"]["expiry_before_separator"][expiry_step]
    expired_admitted = expired_proposal in expiry_case["allowed_by_step"][expiry_step] and expiry_step < expiry_case["expiry_before_step"]
    if expired_admitted:
        errors.append("expired witness incorrectly admitted")
    censored_event = raw.get("refused_action_event", {})
    if (censored_event.get("proposal"), censored_event.get("admitted"), censored_event.get("executed"), censored_event.get("observation")) != (expired_proposal, False, None, None):
        errors.append("refused action counterfactual observation leaked or refusal trace mismatch")

    opportunity = [opportunity_accounting(fixture, truth, state) for state in fixture["prior"]]
    if sum(row["displaced"] for row in opportunity) != 2:
        errors.append("action-induced opportunity displacement not reconstructed")
    if errors:
        return {"status": "FAIL_A02_AUDIT_CONTRACT", "errors": errors, "pair_results": pair_results}
    return {
        "status": "PASS_METHOD_SCOPED",
        "pair_results": pair_results,
        "one_step_information_gain_bits": gain,
        "repeated_same_action_events": len(events),
        "opportunity_accounting": opportunity,
        "authority_grants": 0,
        "refused_observation_leaks": 0,
        "scope": "finite authored model only",
    }


def main(raw_path):
    raw = json.loads(Path(raw_path).read_text())
    fixture = json.loads((ROOT / "fixture.json").read_text())
    truth = json.loads((ROOT / "oracle_truth.json").read_text())
    result = audit(raw, fixture, truth)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if result["status"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: auditor.py RAW.json")
    main(sys.argv[1])

"""Separate exact-rational auditor. Does not import candidate implementation."""

from fractions import Fraction as Q


def _m(values):
    return [[Q(v) for v in row] for row in values]


def _v(values):
    return [Q(v) for v in values]


def _mm(left, right):
    return [[sum((left[i][k] * right[k][j] for k in range(2)), Q(0)) for j in range(2)] for i in range(2)]


def _sum(*matrices):
    return [[sum((m[i][j] for m in matrices), Q(0)) for j in range(2)] for i in range(2)]


def _f(value):
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _gain_status(matrix):
    a, b = matrix[0]
    c, d = matrix[1]
    boundary = (1 - a) * (1 - d) - b * c
    if a > 1 or d > 1 or boundary < 0:
        return "UNSTABLE_ENVELOPE"
    if boundary == 0:
        return "BOUNDED_NONCONVERGENT_ENVELOPE"
    return "STABLE_ENVELOPE"


def _reconstruct(case):
    plant, delayed = _m(case["current"]), _m(case["delayed"])
    actuator, controller, release = _m(case["actuator"]), _m(case["controller"]), _m(case["release"])
    rho = _v(case["release_factor"])
    held = _v(case["hold_requested"])
    decay = [[rho[0], Q(0)], [Q(0), rho[1]]]
    hold_scale = [[held[0], Q(0)], [Q(0), held[1]]]
    loop = _mm(actuator, _mm(hold_scale, controller))
    tail = _mm(release, _mm(decay, loop))
    combined = _sum(plant, delayed, loop, tail)
    components = {"current": plant, "delayed": delayed, "actuator_controller": loop, "release": tail}
    isolated = {name: max(sum(row, Q(0)) for row in values) < 1 for name, values in components.items()}

    states = [_v(case["initial"])]
    residual = [Q(0), Q(0)]
    top = max(abs(z) for z in states[0])
    valid_hold = all(0 <= int(want) <= int(cap) for want, cap in zip(case["hold_requested"], case["hold_limit"]))
    for tick in range(int(case["horizon"])):
        lag = int(case["delay_schedule"][tick % len(case["delay_schedule"])])
        if lag < 0 or lag > tick + 1:
            valid_hold = False
            lag = min(max(0, lag), tick + 1)
        seen = states[max(0, tick - lag)]
        noisy = [seen[i] + Q(case["estimator_error"][i]) for i in range(2)]
        command = [
            min(Q(case["saturation"][i]), max(Q(0), sum((controller[i][j] * noisy[j] for j in range(2)), Q(0))))
            for i in range(2)
        ]
        active = [command[i] * held[i] if held[i] > 0 else Q(0) for i in range(2)]
        next_state = [
            sum((plant[i][j] * states[tick][j] + delayed[i][j] * seen[j] + actuator[i][j] * active[j] + release[i][j] * residual[j] for j in range(2)), Q(0))
            + Q(case["disturbance"][i])
            for i in range(2)
        ]
        residual = [rho[i] * active[i] for i in range(2)]
        states.append(next_state)
        top = max(top, *(abs(z) for z in next_state))
    rows = [sum(line, Q(0)) for line in combined]
    accepted = valid_hold and max(rows) < 1 and top <= Q(case["feature_limit"])
    return {
        "id": case["id"],
        "disposition": "CERTIFIED" if accepted else "NO_COMPOSITION_CERTIFICATE",
        "gain_matrix": [[_f(z) for z in line] for line in combined],
        "gain_envelope_status": _gain_status(combined),
        "max_row_gain": _f(max(rows)),
        "peak_feature": _f(top),
        "crosses_feature_limit": top > Q(case["feature_limit"]),
        "hold_contract_valid": valid_hold,
        "subsystem_checks": isolated,
        "delay_max": max(map(int, case["delay_schedule"])),
        "trajectory": [[_f(z) for z in state] for state in states],
    }, combined, loop, tail


def _matches(expected, submitted):
    keys = ("id", "disposition", "gain_matrix", "gain_envelope_status", "max_row_gain", "peak_feature",
            "crosses_feature_limit", "hold_contract_valid", "subsystem_checks",
            "delay_max", "trajectory")
    return all(submitted.get(key) == expected[key] for key in keys)


def audit(cases, raw):
    mismatches = 0
    unsafe = 0
    rows = []
    for case, submitted in zip(cases, raw):
        expected, _, _, _ = _reconstruct(case)
        rows.append(expected)
        mismatches += int(not _matches(expected, submitted))
        unsafe += int(submitted.get("disposition") == "CERTIFIED" and expected["crosses_feature_limit"])
    rejected = 0
    mutation_case = None
    mutation_expected = None
    mutation_parts = None
    for case in cases:
        reconstructed = _reconstruct(case)
        _, combined_candidate, _, tail_candidate = reconstructed
        has_cross = combined_candidate[0][1] != 0 or combined_candidate[1][0] != 0
        has_release = any(value != 0 for row in tail_candidate for value in row)
        if has_cross and has_release:
            mutation_case, mutation_expected, mutation_parts = case, reconstructed[0], reconstructed[1:]
            break
    if mutation_case is not None:
        expected, combined, loop, tail = mutation_expected, mutation_parts[0], mutation_parts[1], mutation_parts[2]
        mutations = []
        no_coupling = [line[:] for line in combined]
        no_coupling[0][1] = Q(0)
        mutations.append(no_coupling)
        no_release = [[combined[i][j] - tail[i][j] for j in range(2)] for i in range(2)]
        mutations.append(no_release)
        understated = [line[:] for line in combined]
        understated[0][0] = max(Q(0), understated[0][0] - Q(1, 10))
        mutations.append(understated)
        for mutated in mutations:
            forged = dict(expected)
            forged["gain_matrix"] = [[_f(z) for z in line] for line in mutated]
            rejected += int(not _matches(expected, forged))
    count = min(len(cases), len(raw))
    mismatches += int(len(cases) != len(raw))
    actual_by_id = {row.get("id"): row for row in raw}
    gates = {}
    for case_id in (
        "C01_uncoupled_positive", "C02_cross_coupled_unstable",
        "C03_delayed_jitter_shared_actuator_stable", "C04_unit_eigenvalue_boundary",
        "C05_stable_conservative_reject", "C06_release_lag_included",
        "C07_held_input_cap_refusal", "C08_estimator_disturbance_feature_escape",
    ):
        if case_id not in actual_by_id:
            gates[case_id] = False
    for key in ("C01_uncoupled_positive", "C03_delayed_jitter_shared_actuator_stable"):
        row = actual_by_id.get(key, {})
        gates[key] = row.get("disposition") == "CERTIFIED" and not row.get("crosses_feature_limit", True)
    coupled = actual_by_id.get("C02_cross_coupled_unstable", {})
    gates["C02_cross_coupled_unstable"] = (
        coupled.get("disposition") == "NO_COMPOSITION_CERTIFICATE"
        and coupled.get("crosses_feature_limit") is True
        and coupled.get("gain_envelope_status") == "UNSTABLE_ENVELOPE"
        and all(coupled.get("subsystem_checks", {}).values())
    )
    boundary = actual_by_id.get("C04_unit_eigenvalue_boundary", {})
    gates["C04_unit_eigenvalue_boundary"] = (
        boundary.get("disposition") == "NO_COMPOSITION_CERTIFICATE"
        and boundary.get("gain_envelope_status") == "BOUNDED_NONCONVERGENT_ENVELOPE"
    )
    stable_reject = actual_by_id.get("C05_stable_conservative_reject", {})
    gates["C05_stable_conservative_reject"] = (
        stable_reject.get("disposition") == "NO_COMPOSITION_CERTIFICATE"
        and stable_reject.get("gain_envelope_status") == "STABLE_ENVELOPE"
    )
    for key in ("C06_release_lag_included", "C07_held_input_cap_refusal"):
        row = actual_by_id.get(key, {})
        gates[key] = row.get("disposition") == "NO_COMPOSITION_CERTIFICATE"
    cap_row = actual_by_id.get("C07_held_input_cap_refusal", {})
    gates["C07_held_input_cap_refusal"] = gates["C07_held_input_cap_refusal"] and cap_row.get("hold_contract_valid") is False
    escaped = actual_by_id.get("C08_estimator_disturbance_feature_escape", {})
    gates["C08_estimator_disturbance_feature_escape"] = (
        escaped.get("disposition") == "NO_COMPOSITION_CERTIFICATE"
        and escaped.get("crosses_feature_limit") is True
    )
    gates["no_certified_feature_escape"] = unsafe == 0
    audit_ok = count == len(cases) and mismatches == 0 and unsafe == 0 and rejected == 3
    method_ok = audit_ok and all(gates.values())
    return {
        "disposition": "PASS_METHOD_SCOPED" if method_ok else "FAIL_AUDIT",
        "audit_contract": "PASS_AUDIT_SCOPED" if audit_ok else "FAIL_AUDIT",
        "rows_reconstructed": count,
        "row_mismatches": mismatches,
        "unsafe_certificates": unsafe,
        "mutations_rejected": rejected,
        "decision_gates": gates,
        "rows": rows,
    }


if __name__ == "__main__":
    import json
    import sys
    with open(sys.argv[1], encoding="utf-8") as stream:
        frozen_cases = json.load(stream)
    with open(sys.argv[2], encoding="utf-8") as stream:
        candidate_rows = json.load(stream)
    result = audit(frozen_cases, candidate_rows)
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1)

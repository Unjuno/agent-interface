"""Finite-horizon candidate for exact, nonnegative two-feature fixtures."""

from fractions import Fraction as F


def matrix(raw):
    return [[F(v) for v in row] for row in raw]


def matmul(a, b):
    return [[sum((a[i][k] * b[k][j] for k in range(2)), F(0)) for j in range(2)] for i in range(2)]


def add(*items):
    return [[sum((m[i][j] for m in items), F(0)) for j in range(2)] for i in range(2)]


def vec(raw):
    return [F(v) for v in raw]


def fmt(value):
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def matrix_status(gains):
    a, b = gains[0]
    c, d = gains[1]
    delta = (1 - a) * (1 - d) - b * c
    if a > 1 or d > 1 or delta < 0:
        return "UNSTABLE_ENVELOPE"
    if delta == 0:
        return "BOUNDED_NONCONVERGENT_ENVELOPE"
    return "STABLE_ENVELOPE"


def evaluate(case):
    a, d, b, k, r = (matrix(case[name]) for name in ("current", "delayed", "actuator", "controller", "release"))
    rho = vec(case["release_factor"])
    held = [F(v) for v in case["hold_requested"]]
    release_scale = [[rho[0], F(0)], [F(0), rho[1]]]
    hold_scale = [[held[0], F(0)], [F(0), held[1]]]
    loop = matmul(b, matmul(hold_scale, k))
    release_loop = matmul(r, matmul(release_scale, loop))
    gains = add(a, d, loop, release_loop)
    components = {"current": a, "delayed": d, "actuator_controller": loop, "release": release_loop}
    initial = vec(case["initial"])
    states = [initial]
    residual = [F(0), F(0)]
    peak = max(abs(x) for x in initial)
    valid = all(int(req) >= 0 and int(req) <= int(cap) for req, cap in zip(case["hold_requested"], case["hold_limit"]))
    for t in range(int(case["horizon"])):
        delay = int(case["delay_schedule"][t % len(case["delay_schedule"])])
        if delay < 0 or delay > t + 1:
            valid = False
            delay = min(max(delay, 0), t + 1)
        observed_state = states[max(0, t - delay)]
        observed = [observed_state[i] + F(case["estimator_error"][i]) for i in range(2)]
        command = [min(F(case["saturation"][i]), max(F(0), sum((k[i][j] * observed[j] for j in range(2)), F(0)))) for i in range(2)]
        admitted = [command[i] * held[i] if held[i] > 0 else F(0) for i in range(2)]
        now = [
            sum((a[i][j] * states[t][j] + d[i][j] * observed_state[j] + b[i][j] * admitted[j] + r[i][j] * residual[j] for j in range(2)), F(0))
            + F(case["disturbance"][i])
            for i in range(2)
        ]
        residual = [rho[i] * admitted[i] for i in range(2)]
        states.append(now)
        peak = max(peak, *(abs(x) for x in now))
    norm_rows = [sum(row, F(0)) for row in gains]
    subsystem_checks = {name: max(sum(row, F(0)) for row in value) < 1 for name, value in components.items()}
    stable_screen = max(norm_rows) < F(1)
    within_feature = peak <= F(case["feature_limit"])
    disposition = "CERTIFIED" if valid and stable_screen and within_feature else "NO_COMPOSITION_CERTIFICATE"
    return {
        "id": case["id"],
        "disposition": disposition,
        "gain_matrix": [[fmt(x) for x in row] for row in gains],
        "gain_envelope_status": matrix_status(gains),
        "max_row_gain": fmt(max(norm_rows)),
        "peak_feature": fmt(peak),
        "crosses_feature_limit": not within_feature,
        "hold_contract_valid": valid,
        "subsystem_checks": subsystem_checks,
        "delay_max": max(map(int, case["delay_schedule"])),
        "trajectory": [[fmt(x) for x in state] for state in states],
    }


if __name__ == "__main__":
    import json
    import sys
    with open(sys.argv[1], encoding="utf-8") as stream:
        frozen_cases = json.load(stream)
    print(json.dumps([evaluate(case) for case in frozen_cases], indent=2, sort_keys=True))

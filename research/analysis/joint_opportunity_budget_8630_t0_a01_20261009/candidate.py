"""Frozen finite-horizon policy optimizer for Issue #8630 T0 A01."""
from itertools import product

PRIOR = (0.5, 0.5)
P = {
    "informative": {"A": (0.9, 0.2), "B": (0.2, 0.9)},
    "weak_signal": {"A": (0.51, 0.49), "B": (0.49, 0.51)},
}
HORIZON = 4


def expected_verified_success(kind, observe, recover):
    """Compute expected verified success for one declared policy class."""
    remaining = HORIZON - int(observe) - 1 - int(recover) - 1
    if remaining < 0:  # action + mandatory readback do not fit
        return None
    if observe:
        # The observation identifies the type before choosing A or B.
        total = sum(PRIOR[t] * max(P[kind][a][t] for a in ("A", "B")) for t in range(2))
    else:
        # Without the observation, one action must be selected under the prior.
        total = max(sum(PRIOR[t] * P[kind][a][t] for t in range(2)) for a in ("A", "B"))
    if recover:
        total += (1.0 - total) * 0.5
    return total


def solve(kind):
    rows = []
    for observe, recover in product((False, True), repeat=2):
        score = expected_verified_success(kind, observe, recover)
        if score is not None:
            rows.append({"observe": observe, "recover": recover, "score": round(score, 8)})
    return max(rows, key=lambda row: (row["score"], not row["observe"], row["recover"]))


if __name__ == "__main__":
    import json
    print(json.dumps({kind: {"policy": solve(kind), "feasible_policies": [
        {"observe": o, "recover": r, "score": expected_verified_success(kind, o, r)}
        for o, r in product((False, True), repeat=2)
        if expected_verified_success(kind, o, r) is not None
    ]} for kind in P}, sort_keys=True, indent=2))

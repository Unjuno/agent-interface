"""Independent raw-only exhaustive schedule enumerator for T0 A01."""
from itertools import product

CASES = {
    "informative": ((0.9, 0.2), (0.2, 0.9)),
    "weak_signal": ((0.51, 0.49), (0.49, 0.51)),
}


def enumerate_case(matrix):
    scored = []
    for inspect, retry in product((0, 1), repeat=2):
        used = inspect + 1 + retry + 1  # inspect, first action, retry, mandatory readback
        if used > 4:
            continue
        p0, p1 = matrix
        # Without information the action must be fixed before hidden type is known.
        prior_action_values = [(p0[a] + p1[a]) / 2 for a in range(2)]
        if inspect:
            first = (max(p0) + max(p1)) / 2
        else:
            first = max(prior_action_values)
        terminal = first + (1 - first) * 0.5 if retry else first
        scored.append({"observe": bool(inspect), "recover": bool(retry), "score": round(terminal, 8), "used": used})
    return sorted(scored, key=lambda x: (x["score"], not x["observe"], x["recover"]))


if __name__ == "__main__":
    import json
    print(json.dumps({key: enumerate_case(value) for key, value in CASES.items()}, sort_keys=True, indent=2))

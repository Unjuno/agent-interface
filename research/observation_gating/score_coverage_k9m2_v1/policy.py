"""Research-only integer interval calibration. No task or input authority."""
def vector(x, nonnegative=False):
    if not isinstance(x, list) or len(x) != 4:
        raise ValueError("four coordinates required")
    if any(type(v) is not int or (nonnegative and v < 0) for v in x):
        raise ValueError("integer coordinates required; booleans excluded")
    return x


def quantile95(values):
    if len(values) < 19 or any(type(v) is not int or v < 0 for v in values):
        raise ValueError("at least 19 nonnegative residuals required")
    rank = ((len(values) + 1) * 19 + 19) // 20
    return sorted(values)[rank - 1]


def calibrate(residuals):
    for row in residuals:
        vector(row, True)
    marginal = [quantile95([r[i] for r in residuals]) for i in range(4)]
    joint = quantile95([max(r) for r in residuals])
    return {"MARGINAL95": marginal, "JOINT95": [joint] * 4}


def possible_max(scores, radii):
    vector(scores)
    vector(radii, True)
    lower = max(s - q for s, q in zip(scores, radii))
    return [i for i in range(4) if scores[i] + radii[i] >= lower]


def predict(scores, radii):
    vector(scores)
    return {"TOP1_POINT": [max(range(4), key=lambda i: scores[i])],
            **{k: possible_max(scores, radii[k]) for k in ("MARGINAL95", "JOINT95")}}

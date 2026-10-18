"""Frozen finite switched-linear-system protocol for Issue #8471 T0 A01."""
from fractions import Fraction as F

HORIZON = 12
INITIAL = (F(1), F(1, 2))
ENVELOPE = F(4)
DISTURBANCE_ENVELOPE = F(16)
ALPHA = F(5, 6)
MU = F(5)
MIN_DWELL = 10
HYSTERESIS_ENTER = F(2, 3)
HYSTERESIS_EXIT = F(1, 3)
IDENTITY = ((F(1), F(0)), (F(0), F(1)))
MODES = {
    "A": ((F(1, 2), F(1)), (F(0), F(1, 2))),
    "B": ((F(1, 2), F(0)), (F(1), F(1, 2))),
}
LYAPUNOV = {
    "A": ((F(4, 3), F(8, 9)), (F(8, 9), F(116, 27))),
    "B": ((F(116, 27), F(8, 9)), (F(8, 9), F(4, 3))),
}
COMMON_MODES = {"A": ((F(1, 2), F(0)), (F(0), F(1, 2))),
                "B": ((F(1, 2), F(0)), (F(0), F(1, 2)))}
COMMON_P = IDENTITY
COMMON_ALPHA = F(1, 4)
COMMON_MU = F(1)


def matrix_vector(a, x):
    return tuple(sum((a[i][j] * x[j] for j in range(2)), F(0)) for i in range(2))


def matrix_product(a, b):
    return tuple(tuple(sum((a[i][k] * b[k][j] for k in range(2)), F(0))
                       for j in range(2)) for i in range(2))


def transpose(a):
    return tuple(tuple(a[j][i] for j in range(2)) for i in range(2))


def quadratic(p, x):
    return sum((x[i] * p[i][j] * x[j] for i in range(2) for j in range(2)), F(0))


def encode(x):
    return [f"{v.numerator}/{v.denominator}" for v in x]


def parse(v):
    return F(v)


def mode_word(n):
    return tuple("B" if (n >> i) & 1 else "A" for i in range(HORIZON))


def schur_stable(product):
    # Exact second-order Jury/Schur conditions for lambda^2-tr(M)lambda+det(M).
    a, b = product[0]
    c, d = product[1]
    tr, det = a + d, a * d - b * c
    return 1 - tr + det > 0 and 1 + tr + det > 0 and 1 - det > 0


def trajectory(word, modes=MODES, initial=INITIAL, disturbance=False, reset=IDENTITY):
    x = tuple(initial)
    states = [x]
    switches = 0
    switch_prefixes = [0]
    for i, name in enumerate(word):
        old = word[i - 1] if i else name
        if i and name != old:
            switches += 1
            x = matrix_vector(reset, x)
        x = matrix_vector(modes[name], x)
        if disturbance:
            d = (F(1, 100), F((-1) ** i, 100))
            x = (x[0] + d[0], x[1] + d[1])
        states.append(x)
        switch_prefixes.append(switches)
    return states, switch_prefixes


def lyapunov_prefix_bounds(word, alpha=ALPHA, mu=MU):
    s = 0
    out = [F(1)]
    for i, name in enumerate(word):
        if i and name != word[i - 1]:
            s += 1
        out.append(alpha ** (i + 1) * mu ** s)
    return out


def minimum_dwell_schedule(requests, dwell=MIN_DWELL):
    current = "A"
    last_switch = -dwell
    out = []
    for tick, requested in enumerate(requests):
        if requested != current and tick - last_switch >= dwell:
            current = requested
            last_switch = tick
        out.append(current)
    return tuple(out)


def hysteresis_schedule(signals):
    current = "A"
    out = []
    for signal in signals:
        if current == "A" and signal >= HYSTERESIS_ENTER:
            current = "B"
        elif current == "B" and signal <= HYSTERESIS_EXIT:
            current = "A"
        out.append(current)
    return tuple(out)

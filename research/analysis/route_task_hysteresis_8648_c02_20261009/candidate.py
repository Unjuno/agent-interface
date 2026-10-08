#!/usr/bin/env python3
"""Frozen deterministic candidate for Issue #8648 C02."""
import itertools
import json
import math

BETA = (2, 10, 20)
GAMMA = (0.5, 1.5)
DELTA = (2, 10, 20)
THETA = tuple(round(-0.30 + 0.03 * i, 12) for i in range(21))
ARMS = ("COUPLED", "ONE_WAY", "EXOGENOUS_ONLY", "ZERO_FEEDBACK")
RELAX = 0.25
TOL = 1e-10
MAX_STEPS = 10000

def sig(x):
    return 1.0 / (1.0 + math.exp(-x))

def targets(a, q, theta, beta, gamma, delta, arm):
    advantage = theta + gamma * (q - 0.5)
    if arm == "COUPLED":
        return sig(beta * advantage), sig(delta * (a - 0.5))
    if arm == "ONE_WAY":
        return sig(beta * theta), sig(delta * (a - 0.5))
    if arm == "EXOGENOUS_ONLY":
        return sig(beta * advantage), sig(delta * theta)
    if arm == "ZERO_FEEDBACK":
        return sig(beta * theta), 0.5
    raise ValueError(arm)

def spectral_radius(a, q, beta, gamma, delta, arm):
    if arm == "COUPLED":
        aa = beta * gamma * a * (1.0 - a)
        bb = delta * q * (1.0 - q)
        z = math.sqrt(max(0.0, aa * bb))
        return max(abs(1.0 - RELAX + RELAX * z),
                   abs(1.0 - RELAX - RELAX * z))
    return 1.0 - RELAX

print(json.dumps({
    "kind": "META", "beta": list(BETA), "gamma": list(GAMMA),
    "delta": list(DELTA), "theta": list(THETA), "arms": list(ARMS),
    "relax": RELAX, "tolerance": TOL, "max_steps": MAX_STEPS,
    "opportunities": 100, "correct_effects": 100
}, sort_keys=True, separators=(",", ":")))

for beta, gamma, delta in itertools.product(BETA, GAMMA, DELTA):
    for arm in ARMS:
        for direction in ("UP", "DOWN"):
            theta_order = THETA if direction == "UP" else tuple(reversed(THETA))
            for initial in ("LOW", "HIGH"):
                a, q = (0.01, 0.01) if initial == "LOW" else (0.99, 0.99)
                points = []
                for theta in theta_order:
                    converged = False
                    steps = 0
                    for steps in range(1, MAX_STEPS + 1):
                        at, qt = targets(a, q, theta, beta, gamma, delta, arm)
                        an = (1.0 - RELAX) * a + RELAX * at
                        qn = (1.0 - RELAX) * q + RELAX * qt
                        change = max(abs(an - a), abs(qn - q))
                        a, q = an, qn
                        if change < TOL:
                            converged = True
                            break
                    advantage = theta + gamma * (q - 0.5)
                    points.append([
                        round(a, 10), round(q, 10), steps, converged
                    ])
                print(json.dumps({
                    "kind": "PROFILE", "beta": beta, "gamma": gamma,
                    "delta": delta, "arm": arm, "direction": direction,
                    "initial": initial, "opportunities": 100,
                    "correct_effects": 100, "points": points
                }, sort_keys=True, separators=(",", ":")))

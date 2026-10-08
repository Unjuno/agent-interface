#!/usr/bin/env python3
"""Independent raw-only auditor for frozen Issue #8648 C01 candidate JSONL."""
import itertools
import json
import math
import sys

BETAS = (2, 10, 20)
GAMMAS = (0.5, 1.5)
DELTAS = (2, 10, 20)
THETAS = tuple(round(-0.30 + 0.03 * i, 12) for i in range(21))
ARMS = ("COUPLED", "ONE_WAY", "EXOGENOUS_ONLY", "ZERO_FEEDBACK")
RELAX = 0.25
TOL = 1e-10
MAX_STEPS = 10000

def logistic(z):
    return 1.0 / (1.0 + math.exp(-z))

def independently_target(state_a, state_q, theta, beta, gamma, delta, arm):
    d = theta + gamma * (state_q - 0.5)
    route_target = logistic(beta * (theta if arm in ("ONE_WAY", "ZERO_FEEDBACK") else d))
    if arm in ("COUPLED", "ONE_WAY"):
        mix_target = logistic(delta * (state_a - 0.5))
    elif arm == "EXOGENOUS_ONLY":
        mix_target = logistic(delta * theta)
    elif arm == "ZERO_FEEDBACK":
        mix_target = 0.5
    else:
        raise ValueError(arm)
    return route_target, mix_target

def independent_radius(a, q, beta, gamma, delta, arm):
    if arm != "COUPLED":
        return 0.75
    route_slope = beta * gamma * a * (1 - a)
    mix_slope = delta * q * (1 - q)
    s = math.sqrt(max(0.0, route_slope * mix_slope))
    return max(abs(0.75 + RELAX * s), abs(0.75 - RELAX * s))

def reconstruct(beta, gamma, delta, arm, direction, initial):
    order = THETAS if direction == "UP" else tuple(reversed(THETAS))
    a, q = (0.01, 0.01) if initial == "LOW" else (0.99, 0.99)
    out = []
    for theta in order:
        ok = False
        count = 0
        for count in range(1, MAX_STEPS + 1):
            ta, tq = independently_target(a, q, theta, beta, gamma, delta, arm)
            next_a = 0.75 * a + RELAX * ta
            next_q = 0.75 * q + RELAX * tq
            err = max(abs(next_a - a), abs(next_q - q))
            a, q = next_a, next_q
            if err < TOL:
                ok = True
                break
        benefit = theta + gamma * (q - 0.5)
        out.append([
            round(a, 10), round(q, 10), count, ok
        ])
    return out

raw = [json.loads(line) for line in sys.stdin if line.strip()]
errors = []
meta = [x for x in raw if x.get("kind") == "META"]
profiles = [x for x in raw if x.get("kind") == "PROFILE"]
if len(meta) != 1:
    errors.append("metadata cardinality mismatch")
else:
    m = meta[0]
    want_meta = {
        "beta": list(BETAS), "gamma": list(GAMMAS), "delta": list(DELTAS),
        "theta": list(THETAS), "arms": list(ARMS), "relax": RELAX,
        "tolerance": TOL, "max_steps": MAX_STEPS,
        "opportunities": 100, "correct_effects": 100
    }
    if any(m.get(k) != v for k, v in want_meta.items()):
        errors.append("metadata/freeze mismatch")
expected_keys = {
    (b, g, d, arm, direction, initial)
    for b, g, d in itertools.product(BETAS, GAMMAS, DELTAS)
    for arm in ARMS for direction in ("UP", "DOWN")
    for initial in ("LOW", "HIGH")
}
def key(x):
    return (x.get("beta"), x.get("gamma"), x.get("delta"), x.get("arm"),
            x.get("direction"), x.get("initial"))
keys = [key(x) for x in profiles]
if len(profiles) != 1024 or len(set(keys)) != 1024 or set(keys) != expected_keys:
    errors.append("profile identity/cardinality mismatch")
lookup = {}
for row in profiles:
    k = key(row)
    lookup[k] = row
    if row.get("opportunities") != 100 or row.get("correct_effects") != 100:
        errors.append(f"fixed opportunity/correctness gate changed: {k}")
        continue
    if row.get("arm") not in ARMS or row.get("direction") not in ("UP", "DOWN") or row.get("initial") not in ("LOW", "HIGH"):
        errors.append(f"unknown profile factor: {k}")
        continue
    expected_points = reconstruct(*k)
    got = row.get("points")
    if not isinstance(got, list) or len(got) != len(THETAS):
        errors.append(f"theta profile length mismatch: {k}")
        continue
    if any(len(a) != len(b) or any(
        (isinstance(x, float) or isinstance(y, float)) and
        (not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or abs(x-y) > 1e-10)
        or (not isinstance(x, float) and not isinstance(y, float) and x != y)
        for x, y in zip(a, b)
    ) for a, b in zip(got, expected_points)):
        errors.append(f"trajectory reconstruction mismatch: {k}")

# Five mutation probes are applied only in memory to a representative supported row.
probe_key = (20, 2.0, 20, "COUPLED", "UP", "HIGH")
probe = lookup.get(probe_key)
mutations_rejected = 0
def accepts(row):
    if row.get("opportunities") != 100 or row.get("correct_effects") != 100:
        return False
    k = key(row)
    if k not in expected_keys:
        return False
    try:
        return row.get("points") == reconstruct(*k)
    except Exception:
        return False
if probe:
    altered = []
    a = dict(probe); a["arm"] = "ONE_WAY"; altered.append(a)
    a = dict(probe); a["beta"] = 10; altered.append(a)
    a = json.loads(json.dumps(probe)); a["points"][10][0] += 0.1; altered.append(a)
    a = json.loads(json.dumps(probe)); a["points"][10][2] += 1; altered.append(a)
    a = dict(probe); a["correct_effects"] = 99; altered.append(a)
    mutations_rejected = sum(not accepts(x) for x in altered)
if mutations_rejected != 5:
    errors.append(f"mutation controls rejected {mutations_rejected}/5")

def contiguous_at_least_three(flags):
    run = 0
    for flag in flags:
        run = run + 1 if flag else 0
        if run >= 3:
            return True
    return False

heldout_regions = []
control_regions = {arm: 0 for arm in ARMS if arm != "COUPLED"}
for beta, gamma in itertools.product(BETAS, GAMMAS):
    coupled_flags = []
    for idx in range(len(THETAS)):
        lo = lookup.get((beta, gamma, 20, "COUPLED", "UP", "LOW"))
        hi = lookup.get((beta, gamma, 20, "COUPLED", "UP", "HIGH"))
        if not lo or not hi:
            coupled_flags.append(False); continue
        lp, hp = lo["points"][idx], hi["points"][idx]
        coupled_flags.append(
            lp[3] and hp[3] and independent_radius(lp[0], lp[1], beta, gamma, 20, "COUPLED") < 0.99 and independent_radius(hp[0], hp[1], beta, gamma, 20, "COUPLED") < 0.99
            and abs(lp[0] - hp[0]) >= 0.25
            and abs((100*lp[0]*(THETAS[idx] + gamma*(lp[1]-0.5))) - (100*hp[0]*(THETAS[idx] + gamma*(hp[1]-0.5)))) >= 0.05
        )
    if contiguous_at_least_three(coupled_flags):
        heldout_regions.append((beta, gamma))
for arm in control_regions:
    for beta, gamma in itertools.product(BETAS, GAMMAS):
        flags = []
        for idx in range(len(THETAS)):
            lo = lookup.get((beta, gamma, 20, arm, "UP", "LOW"))
            hi = lookup.get((beta, gamma, 20, arm, "UP", "HIGH"))
            if not lo or not hi:
                flags.append(False); continue
            lp, hp = lo["points"][idx], hi["points"][idx]
            flags.append(
                lp[3] and hp[3] and independent_radius(lp[0], lp[1], beta, gamma, 20, arm) < 0.99 and independent_radius(hp[0], hp[1], beta, gamma, 20, arm) < 0.99
                and abs(lp[0] - hp[0]) >= 0.25
                and abs((100*lp[0]*(THETAS[idx] + gamma*(lp[1]-0.5))) - (100*hp[0]*(THETAS[idx] + gamma*(hp[1]-0.5)))) >= 0.05
            )
        if contiguous_at_least_three(flags):
            control_regions[arm] += 1
nonconverged = sum(not p[3] for row in profiles for p in row.get("points", []))
if errors:
    status = "FAIL_METHOD"
else:
    status = "PASS_METHOD_SCOPED"
h_pass = len(heldout_regions) >= 3 and all(n == 0 for n in control_regions.values()) and nonconverged == 0
result = {
    "status": status, "hypothesis": "H_PASS_SCOPED" if h_pass and status == "PASS_METHOD_SCOPED" else ("NO_HYSTERESIS_SCOPED" if status == "PASS_METHOD_SCOPED" else "NOT_EVALUABLE"),
    "raw_rows": len(raw), "profiles": len(profiles), "expected_profiles": 288,
    "heldout_parameter_regions": [list(x) for x in heldout_regions],
    "heldout_region_count": len(heldout_regions), "control_region_counts": control_regions,
    "nonconverged_endpoints": nonconverged,
    "mutations_rejected": mutations_rejected, "mutations_total": 5,
    "errors": errors, "scope": "authored deterministic route/task-mix dynamical model only"
}
print(json.dumps(result, sort_keys=True, indent=2))
sys.exit(0 if status != "FAIL_METHOD" else 1)

"""Two image-only bounded correction policies; no access to simulator truth."""
from __future__ import annotations

import math


def norm(v):
    return math.hypot(v[0], v[1])


def cap(v, maximum):
    n = norm(v)
    return [v[0] * maximum / n, v[1] * maximum / n] if n > maximum else list(v)


def solve(m, v):
    det = m[0][0] * m[1][1] - m[0][1] * m[1][0]
    if not math.isfinite(det) or abs(det) < 0.08:
        return None
    return [(m[1][1] * v[0] - m[0][1] * v[1]) / det,
            (-m[1][0] * v[0] + m[0][0] * v[1]) / det]


def run_trial(arm, observe, act, *, max_corrections=24, tolerance=1.0,
              max_action=12.0, gain=0.75):
    """Use fresh same-generation feature observations; stop on invalid identity/model."""
    target = observe()
    generation = target["generation"]
    identity = target["target_id"]
    error = list(target["error"])
    jac = [[1.0, 0.0], [0.0, 1.0]]
    prior_action = prior_error = None
    rows = []
    for step in range(max_corrections):
        if norm(error) <= tolerance:
            return {"status": "reached", "corrections": step, "rows": rows}
        if arm == "online_jacobian" and prior_action is not None:
            # Secant/Broyden update from an already-required action and fresh image.
            de = [prior_error[i] - error[i] for i in range(2)]
            residual = [de[i] - sum(jac[i][j] * prior_action[j] for j in range(2))
                        for i in range(2)]
            denominator = sum(x*x for x in prior_action)
            if denominator < 1e-8:
                return {"status": "yield_ill_conditioned", "corrections": step, "rows": rows}
            jac = [[jac[i][j] + residual[i] * prior_action[j] / denominator for j in range(2)]
                   for i in range(2)]
        desired = [gain * x for x in error]
        action = solve(jac, desired) if arm == "online_jacobian" else desired
        if action is None:
            return {"status": "yield_ill_conditioned", "corrections": step, "rows": rows}
        action = cap(action, max_action)
        receipt = act(action)
        sample = observe()
        if (sample["generation"] != generation or sample["target_id"] != identity
                or not sample["fresh"] or not receipt["acknowledged"]):
            return {"status": "yield_unbound_or_stale", "corrections": step + 1, "rows": rows}
        new_error = list(sample["error"])
        rows.append({"step": step, "before": error, "action": action,
                     "after": new_error, "generation": generation})
        prior_action, prior_error = action, error
        error = new_error
    return {"status": "budget_exhausted", "corrections": max_corrections, "rows": rows}

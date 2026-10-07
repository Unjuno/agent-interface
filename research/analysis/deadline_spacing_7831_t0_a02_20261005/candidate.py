"""Candidate deadline-constrained spacing selector for Issue #7831 A02."""

import fixtures

POLICIES = ("FIXED_PERIOD", "RAW_EVENT", "HYSTERESIS", "DEADLINE_SPACED")


def _ceil_div(a, b):
    return (a + b - 1) // b


def _plan_next(tick, margin, uncertainty, cfg, trace):
    remaining = margin - uncertainty
    rate = cfg["decline_bound"] + cfg["uncertainty_growth"]
    if remaining <= 0:
        return "CONFLICT", None
    if rate == 0:
        return "CENSORED", None
    if remaining - rate * (trace["horizon"] - tick + cfg["latency"]) > 0:
        return "CENSORED", None
    latest = tick + _ceil_div(remaining, rate) - 1 - cfg["latency"]
    earliest = tick + cfg["minimum_spacing"]
    horizon = trace["horizon"]
    if latest > horizon:
        return "CENSORED", None
    if earliest > horizon:
        if remaining - rate * (horizon - tick + cfg["latency"]) > 0:
            return "CENSORED", None
        return "CONFLICT", None
    if latest < earliest:
        return "CONFLICT", None
    return "SCHEDULE", latest


def _release_result(name, policy, trace, cfg, ticks, suppressed, unknown,
                    release, reason, hard_tick=None):
    unsafe = next((i for i, value in enumerate(trace["margin"])
                   if value - cfg["uncertainty_growth"] * i <= 0), None)
    violations = int(unsafe is not None and
                     (release is None or release >= unsafe))
    hard_suppressed = int(bool(trace["hard"]) and
                          (hard_tick is None or reason != "HARD_BYPASS"))
    return {"trace": name, "policy": policy, "optional_ticks": ticks,
            "optional_count": len(ticks), "suppressed_cues": suppressed,
            "unknown_intervals": unknown, "release_tick": release,
            "reason": reason, "unsafe_tick": unsafe,
            "boundary_violations": violations,
            "hard_bypass_suppressed": hard_suppressed,
            "bypass_latency": (release - hard_tick if hard_tick is not None
                               else None)}


def _sample_decision(tick, trace, cfg):
    if tick in trace["missing"]:
        return "MISSING_MEASUREMENT"
    if tick in trace.get("delayed", []):
        return "DELAYED_MEASUREMENT"
    margin = trace["margin"][tick]
    uncertainty = cfg["uncertainty_growth"] * tick
    rate = cfg["decline_bound"] + cfg["uncertainty_growth"]
    if margin - uncertainty - rate * cfg["latency"] <= 0:
        return "DEADLINE_NEAR"
    return "CONTINUE"


def _baseline(name, trace, cfg, policy):
    horizon = trace["horizon"]
    if policy == "RAW_EVENT":
        requested = [t for t in range(1, horizon + 1)
                     if trace["signal"][t] <= 1]
    elif policy == "FIXED_PERIOD":
        requested = list(range(cfg["fixed_period"], horizon + 1,
                               cfg["fixed_period"]))
    else:
        requested = []
        armed = True
        for t in range(1, horizon + 1):
            if armed and trace["signal"][t] <= 1:
                requested.append(t)
                armed = False
            elif not armed and trace["signal"][t] >= 4:
                armed = True
    ticks, unknown, release, reason, hard_tick = [], 0, None, "HORIZON_CENSORED", None
    budget = trace["budget"]
    for tick in range(1, horizon + 1):
        if tick in trace["hard"]:
            hard_tick, release, reason = tick, tick + cfg["latency"], "HARD_BYPASS"
            break
        if tick not in requested:
            continue
        if len(ticks) >= budget:
            release, reason = tick + cfg["latency"], "BUDGET_EXHAUSTED"
            break
        ticks.append(tick)
        decision = _sample_decision(tick, trace, cfg)
        if decision in ("MISSING_MEASUREMENT", "DELAYED_MEASUREMENT"):
            unknown += 1
            release, reason = tick + cfg["latency"], decision
            break
        if decision != "CONTINUE":
            release, reason = tick + cfg["latency"], decision
            break
    sampled = set(ticks)
    suppressed = sum(1 for tick in requested if tick not in sampled and
                     (release is None or tick <= release))
    return _release_result(name, policy, trace, cfg, ticks, suppressed,
                           unknown, release, reason, hard_tick)


def _deadline_spaced(name, trace, cfg):
    horizon = trace["horizon"]
    due_state, due = _plan_next(
        0, trace["margin"][0], 0, cfg, trace)
    ticks, unknown, release, reason, hard_tick = [], 0, None, "HORIZON_CENSORED", None
    current = 0
    if due_state == "CONFLICT":
        release, reason = cfg["latency"], "SPACING_DEADLINE_CONFLICT"
    else:
        while due_state == "SCHEDULE":
            intervening_hard = next((x for x in trace["hard"]
                                     if current < x <= due), None)
            if intervening_hard is not None:
                hard_tick = intervening_hard
                release = hard_tick + cfg["latency"]
                reason = "HARD_BYPASS"
                break
            if due > horizon:
                break
            ticks.append(due)
            decision = _sample_decision(due, trace, cfg)
            if decision in ("MISSING_MEASUREMENT", "DELAYED_MEASUREMENT"):
                unknown += 1
                release, reason = due + cfg["latency"], decision
                break
            if decision != "CONTINUE":
                release, reason = due + cfg["latency"], decision
                break
            due_state, due = _plan_next(
                due, trace["margin"][due], cfg["uncertainty_growth"] * due,
                cfg, trace)
            current = ticks[-1]
            if due_state == "CONFLICT":
                release = current + cfg["latency"]
                reason = "SPACING_DEADLINE_CONFLICT"
                break
            if due_state == "SCHEDULE" and len(ticks) >= trace["budget"]:
                if due <= horizon:
                    release = current + cfg["latency"]
                    reason = "BUDGET_EXHAUSTED"
                    break
                due_state = "CENSORED"
    if release is None and trace["hard"]:
        future_hard = [event for event in trace["hard"] if event > current]
        if future_hard:
            hard_tick = min(future_hard)
            release = hard_tick + cfg["latency"]
            reason = "HARD_BYPASS"
    sampled = set(ticks)
    suppressed = sum(1 for tick in range(1, horizon + 1)
                     if trace["signal"][tick] <= 1 and tick not in sampled and
                     (release is None or tick <= release))
    return _release_result(name, "DEADLINE_SPACED", trace, cfg, ticks,
                           suppressed, unknown, release, reason, hard_tick)


def evaluate(name, trace, cfg):
    rows = {policy: _baseline(name, trace, cfg, policy)
            for policy in POLICIES if policy != "DEADLINE_SPACED"}
    rows["DEADLINE_SPACED"] = _deadline_spaced(name, trace, cfg)
    return rows


def all_results():
    corpus = fixtures.traces()
    return [{"config": cfg, "trace": name,
             "rows": evaluate(name, trace, cfg)}
            for cfg in fixtures.sensitivity_grid()
            for name, trace in corpus.items()]

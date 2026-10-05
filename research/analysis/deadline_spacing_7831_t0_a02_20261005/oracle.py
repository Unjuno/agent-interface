"""Independent exhaustive tick oracle for Issue #7831 A02."""

from math import inf

POLICIES = ("FIXED_PERIOD", "RAW_EVENT", "HYSTERESIS", "DEADLINE_SPACED")


def _ceil_ratio(n, d):
    q, r = divmod(n, d)
    return q + bool(r)


def _enumerate_next(tick, margin, uncertainty, cfg, trace):
    x = margin - uncertainty
    rate = cfg["decline_bound"] + cfg["uncertainty_growth"]
    horizon = trace["horizon"]
    if x <= 0:
        return "CONFLICT", None
    if rate == 0:
        return "CENSORED", None
    if x - rate * (horizon - tick + cfg["latency"]) > 0:
        return "CENSORED", None
    feasible = []
    for slot in range(tick + cfg["minimum_spacing"], horizon + 1):
        release_slot = slot + cfg["latency"]
        if x - rate * (release_slot - tick) > 0:
            feasible.append(slot)
    if feasible:
        return "SCHEDULE", max(feasible)
    horizon_release = horizon + cfg["latency"]
    if x - rate * (horizon_release - tick) > 0:
        return "CENSORED", None
    return "CONFLICT", None


def _actual_unsafe(trace, cfg):
    return next((i for i, m in enumerate(trace["margin"])
                 if m - cfg["uncertainty_growth"] * i <= 0), None)


def _record(name, policy, trace, cfg, ticks, suppressed, unknown, release,
            reason, hard_tick=None):
    unsafe = _actual_unsafe(trace, cfg)
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


def _baseline(name, trace, cfg, policy):
    h = trace["horizon"]
    if policy == "RAW_EVENT":
        wanted = [t for t in range(1, h + 1) if trace["signal"][t] <= 1]
    elif policy == "FIXED_PERIOD":
        wanted = list(range(cfg["fixed_period"], h + 1, cfg["fixed_period"]))
    else:
        wanted, armed = [], True
        for t in range(1, h + 1):
            if armed and trace["signal"][t] <= 1:
                wanted.append(t)
                armed = False
            elif not armed and trace["signal"][t] >= 4:
                armed = True
    ticks, unknown, release = [], 0, None
    reason, hard_tick = "HORIZON_CENSORED", None
    for t in range(1, h + 1):
        if t in trace["hard"]:
            hard_tick, release = t, t + cfg["latency"]
            reason = "HARD_BYPASS"
            break
        if t not in wanted:
            continue
        if len(ticks) >= trace["budget"]:
            release, reason = t + cfg["latency"], "BUDGET_EXHAUSTED"
            break
        ticks.append(t)
        if t in trace["missing"] or t in trace.get("delayed", []):
            unknown += 1
            kind = ("DELAYED_MEASUREMENT" if t in trace.get("delayed", [])
                    else "MISSING_MEASUREMENT")
            release, reason = t + cfg["latency"], kind
            break
        x = trace["margin"][t] - cfg["uncertainty_growth"] * t
        rate = cfg["decline_bound"] + cfg["uncertainty_growth"]
        if x - rate * cfg["latency"] <= 0:
            release, reason = t + cfg["latency"], "DEADLINE_NEAR"
            break
    sampled = set(ticks)
    suppressed = sum(1 for t in wanted if t not in sampled and
                     (release is None or t <= release))
    return _record(name, policy, trace, cfg, ticks, suppressed, unknown,
                   release, reason, hard_tick)


def _spaced(name, trace, cfg):
    h = trace["horizon"]
    state, due = _enumerate_next(0, trace["margin"][0], 0, cfg, trace)
    ticks, unknown, release = [], 0, None
    reason, hard_tick, current = "HORIZON_CENSORED", None, 0
    if state == "CONFLICT":
        release, reason = cfg["latency"], "SPACING_DEADLINE_CONFLICT"
    else:
        while state == "SCHEDULE":
            ahead = [x for x in trace["hard"] if current < x <= due]
            if ahead:
                hard_tick = min(ahead)
                release, reason = hard_tick + cfg["latency"], "HARD_BYPASS"
                break
            if due > h:
                break
            ticks.append(due)
            if due in trace["missing"] or due in trace.get("delayed", []):
                unknown += 1
                kind = ("DELAYED_MEASUREMENT" if due in trace.get("delayed", [])
                        else "MISSING_MEASUREMENT")
                release, reason = due + cfg["latency"], kind
                break
            x = trace["margin"][due] - cfg["uncertainty_growth"] * due
            rate = cfg["decline_bound"] + cfg["uncertainty_growth"]
            if x - rate * cfg["latency"] <= 0:
                release, reason = due + cfg["latency"], "DEADLINE_NEAR"
                break
            state, due = _enumerate_next(
                due, trace["margin"][due],
                cfg["uncertainty_growth"] * due, cfg, trace)
            current = ticks[-1]
            if state == "CONFLICT":
                release = current + cfg["latency"]
                reason = "SPACING_DEADLINE_CONFLICT"
                break
            if state == "SCHEDULE" and len(ticks) >= trace["budget"]:
                if due <= h:
                    release = current + cfg["latency"]
                    reason = "BUDGET_EXHAUSTED"
                    break
                state = "CENSORED"
    if release is None and trace["hard"]:
        future_hard = [event for event in trace["hard"] if event > current]
        if future_hard:
            hard_tick = min(future_hard)
            release = hard_tick + cfg["latency"]
            reason = "HARD_BYPASS"
    sampled = set(ticks)
    suppressed = sum(1 for t in range(1, h + 1)
                     if trace["signal"][t] <= 1 and t not in sampled and
                     (release is None or t <= release))
    return _record(name, "DEADLINE_SPACED", trace, cfg, ticks, suppressed,
                   unknown, release, reason, hard_tick)


def reconstruct(name, trace, cfg):
    rows = {p: _baseline(name, trace, cfg, p)
            for p in POLICIES if p != "DEADLINE_SPACED"}
    rows["DEADLINE_SPACED"] = _spaced(name, trace, cfg)
    return rows


def assert_matches(candidate_rows, source):
    for row in candidate_rows:
        name, cfg = row["trace"], row["config"]
        expected = reconstruct(name, source[name], cfg)
        if row["rows"] != expected:
            raise AssertionError((name, cfg, expected, row["rows"]))
    return len(candidate_rows), sum(len(row["rows"]) for row in candidate_rows)


def exhaustive_latest_slot(tick, margin, uncertainty, cfg, trace):
    state, slot = _enumerate_next(tick, margin, uncertainty, cfg, trace)
    return state, slot

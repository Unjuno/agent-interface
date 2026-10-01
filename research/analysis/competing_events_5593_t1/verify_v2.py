"""Issue #5593 v2: frozen cohort-size and event-type construction controls."""

from fractions import Fraction


ALLOWED = {"success", "stop", "failure", "censor"}


def validate(rows, expected_n):
    if len(rows) != expected_n:
        raise ValueError("cohort size mismatch")
    ids = [episode for episode, _, _ in rows]
    if len(set(ids)) != expected_n:
        raise ValueError("duplicate launch ID")
    if any(not isinstance(t, int) or t < 0 or kind not in ALLOWED
           for _, t, kind in rows):
        raise ValueError("invalid time or terminal type")


def incidence(rows, expected_n, deadline):
    validate(rows, expected_n)
    alive = Fraction(1)
    success_mass = Fraction(0)
    for t in sorted({time for _, time, _ in rows if time <= deadline}):
        risk = sum(time >= t for _, time, _ in rows)
        success = sum(time == t and kind == "success" for _, time, kind in rows)
        absorbed = sum(time == t and kind in {"success", "stop", "failure"}
                       for _, time, kind in rows)
        success_mass += alive * Fraction(success, risk)
        alive *= 1 - Fraction(absorbed, risk)
    return success_mass


def independent_event_table(rows, expected_n, deadline):
    """Audit using grouped event counts and a distinct mass-flow reduction."""
    validate(rows, expected_n)
    counts = {}
    for _, time, kind in rows:
        counts.setdefault(time, {k: 0 for k in ALLOWED})[kind] += 1
    at_risk = expected_n
    live_mass = Fraction(1)
    answer = Fraction(0)
    for t, group in sorted(counts.items()):
        if t > deadline:
            break
        event_count = group["success"] + group["stop"] + group["failure"]
        answer += live_mass * Fraction(group["success"], at_risk)
        live_mass = live_mass * Fraction(at_risk - event_count, at_risk)
        at_risk -= event_count + group["censor"]
    return answer


def wrong_km(rows, expected_n, deadline):
    validate(rows, expected_n)
    survival = Fraction(1)
    for t in sorted({time for _, time, _ in rows if time <= deadline}):
        risk = sum(time >= t for _, time, _ in rows)
        successes = sum(time == t and kind == "success" for _, time, kind in rows)
        survival *= Fraction(risk - successes, risk)
    return 1 - survival


def cohort(groups):
    events = [(time, kind) for time, kind, count in groups for _ in range(count)]
    return [(f"e{i:02d}", time, kind) for i, (time, kind) in enumerate(events)]


complete = cohort([(1, "stop", 2), (2, "success", 4), (3, "failure", 4)])
censored = cohort([(1, "censor", 2), (2, "stop", 2),
                   (3, "success", 3), (4, "failure", 3)])
assert incidence(complete, 10, 2) == independent_event_table(complete, 10, 2) == Fraction(2, 5)
assert wrong_km(complete, 10, 2) == Fraction(1, 2)
assert incidence(censored, 10, 3) == independent_event_table(censored, 10, 3) == Fraction(3, 8)
assert wrong_km(censored, 10, 3) == Fraction(1, 2)

corruptions = {
    "missing_row": complete[:-1],
    "duplicate_id": complete[:-1] + [(complete[0][0], 3, "failure")],
    "unknown_event": complete[:-1] + [(complete[-1][0], 3, "unknown")],
    "invalid_clock": complete[:-1] + [(complete[-1][0], -1, "failure")],
}
for name, rows in corruptions.items():
    try:
        incidence(rows, 10, 3)
    except ValueError:
        continue
    raise AssertionError(f"{name} corruption accepted")

print({"complete_incidence_t2": "2/5", "complete_wrong_KM_t2": "1/2",
       "censored_incidence_t3": "3/8", "censored_wrong_KM_t3": "1/2",
       "corruptions_rejected": list(corruptions)})


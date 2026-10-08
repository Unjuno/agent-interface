"""Issue #5593 construction-only exact competing-event controls.

This is not an empirical agent cohort or a censoring-assumption validation.
"""

from fractions import Fraction


def cumulative_incidence(rows, deadline):
    ids = [row[0] for row in rows]
    assert len(ids) == len(set(ids)), "duplicate launch ID"
    assert all(t >= 0 and kind in {"success", "stop", "failure", "censor"}
               for _, t, kind in rows), "invalid event"
    survival = Fraction(1)
    incidence = Fraction(0)
    for time in sorted({t for _, t, _ in rows if t <= deadline}):
        at_risk = sum(t >= time for _, t, _ in rows)
        success = sum(t == time and kind == "success" for _, t, kind in rows)
        competing = sum(t == time and kind in {"stop", "failure"}
                        for _, t, kind in rows)
        incidence += survival * Fraction(success, at_risk)
        survival *= 1 - Fraction(success + competing, at_risk)
    return incidence


def naive_success_km(rows, deadline):
    survival = Fraction(1)
    for time in sorted({t for _, t, _ in rows if t <= deadline}):
        at_risk = sum(t >= time for _, t, _ in rows)
        success = sum(t == time and kind == "success" for _, t, kind in rows)
        survival *= 1 - Fraction(success, at_risk)
    return 1 - survival


def independent_product(rows, deadline):
    # Independently enumerate event-time transition masses rather than
    # accumulating a cause-specific hazard over the observed risk set.
    mass = Fraction(1)
    success_mass = Fraction(0)
    for time in sorted({t for _, t, _ in rows if t <= deadline}):
        exposed = [row for row in rows if row[1] >= time]
        count = lambda kind: sum(row[1] == time and row[2] == kind for row in exposed)
        success_mass += mass * Fraction(count("success"), len(exposed))
        mass *= Fraction(len(exposed) - count("success") - count("stop")
                         - count("failure"), len(exposed))
    return success_mass


def case(*groups):
    return [(f"e{i:02}", time, kind)
            for i, (time, kind) in enumerate(
                (item for time, kind, count in groups for item in [(time, kind)] * count))]


uncensored = case((1, "stop", 2), (2, "success", 4), (3, "failure", 4))
censored = case((1, "censor", 2), (2, "stop", 2),
                (3, "success", 3), (4, "failure", 3))

assert cumulative_incidence(uncensored, 2) == Fraction(2, 5)
assert independent_product(uncensored, 2) == Fraction(2, 5)
assert naive_success_km(uncensored, 2) == Fraction(1, 2)
assert cumulative_incidence(censored, 3) == Fraction(3, 8)
assert independent_product(censored, 3) == Fraction(3, 8)
assert naive_success_km(censored, 3) == Fraction(1, 2)

for bad in (uncensored + [uncensored[0]],
            uncensored[:-1] + [(uncensored[-1][0], 3, "unknown")]):
    try:
        cumulative_incidence(bad, 3)
    except AssertionError:
        continue
    raise AssertionError("corrupt row accepted")

print({"uncensored_AJ_t2": "2/5", "uncensored_wrong_KM_t2": "1/2",
       "censored_AJ_t3": "3/8", "censored_wrong_KM_t3": "1/2",
       "duplicate_and_unknown_event_rejected": True})


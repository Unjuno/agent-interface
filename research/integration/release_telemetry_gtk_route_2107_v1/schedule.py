"""Frozen, dependency-free arm schedule for Issue #2107's GTK route."""

DELAY_MS = (120, 180, 240, 120, 180, 240, 120, 180)
CONDITIONS = ("NO_RELEASE_RECEIPT", "VALID_RELEASE_RECEIPT", "AMBIGUOUS_RECEIPT")


def schedule(mode: str):
    if mode == "construction":
        return [
            ("NO_RELEASE_RECEIPT", "before", 120, 120, 0),
            ("VALID_RELEASE_RECEIPT", "after", 120, 0, 0),
            ("AMBIGUOUS_RECEIPT", "after", 120, 0, 0),
            ("CONTRADICTORY_EFFECT", "none", 0, 0, 0),
        ]
    if mode != "formal":
        raise ValueError(f"unknown_schedule_mode:{mode}")
    rows = []
    for rep, delay in enumerate(DELAY_MS):
        offset = rep % len(CONDITIONS)
        order = CONDITIONS[offset:] + CONDITIONS[:offset]
        scenarios = ("before", "after") if rep % 2 == 0 else ("after", "before")
        for scenario in scenarios:
            for condition in order:
                rows.append((condition, scenario, delay,
                             delay if scenario == "before" else 0, rep + 1))
        rows.append(("CONTRADICTORY_EFFECT", "none", 0, 0, rep + 1))
    return rows

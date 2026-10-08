"""Finite, label-blind selector mechanics for Issue #5764 T0."""


def _effect_rank(row):
    signal = row.get("effect")
    if signal is None:
        return -1
    if "action_id" in row or "effect_action_id" in row:
        action_id = row.get("action_id")
        effect_action_id = row.get("effect_action_id")
        if not action_id or action_id != effect_action_id:
            return 0
    return int(signal == 1)


def rank_optional(rows, policy, budget):
    """Return optional event IDs in frozen deterministic priority order."""
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    candidates = [row for row in rows if not row["mandatory"]]

    if policy == "DUAL":
        candidates.sort(key=lambda row: (
            -_effect_rank(row), -int(row["novelty"]), row["event_id"]))
    elif policy == "EFFECT_ONLY":
        candidates.sort(key=lambda row: (-_effect_rank(row), row["event_id"]))
    elif policy == "NOVELTY_ONLY":
        candidates.sort(key=lambda row: (-int(row["novelty"]), row["event_id"]))
    elif policy == "5435_SEVERITY_ONLY":
        candidates = [row for row in candidates if row["severity"] >= 2]
    elif policy == "5435_SAFE_IDENTITY_BATCH":
        seen_entities = set()
        kept = []
        for row in candidates:
            score = row.get("score")
            low_confidence = score is not None and score <= 0.1
            suppress = (row["severity"] < 2 and low_confidence
                        and row["entity_id"] in seen_entities)
            if not suppress:
                kept.append(row)
                seen_entities.add(row["entity_id"])
        candidates = kept
    elif policy == "CHRONOLOGICAL":
        candidates.sort(key=lambda row: (row["time"], row["event_id"]))
    else:
        raise ValueError(f"unknown policy: {policy}")

    return [row["event_id"] for row in candidates[:budget]]

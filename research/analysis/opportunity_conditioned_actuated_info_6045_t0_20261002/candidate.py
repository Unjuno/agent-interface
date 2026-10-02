"""Finite synthetic opportunity-conditioned age candidate; no runtime authority."""


def limits(item, scalar, interval):
    pair = item.get(interval)
    return (pair[0], pair[1]) if pair is not None else (item[scalar], item[scalar])


def derive(row):
    comparable = row.get("clock_comparable", True) is True
    delivery = []
    for obs in row["observations"]:
        g0, g1 = limits(obs, "generation", "generation_interval")
        d0, d1 = limits(obs, "delivery", "delivery_interval")
        ordered = comparable and g1 < d0
        interval = [d0 - g1, d1 - g0] if ordered else None
        delivery.append({"observation_id": obs["id"], "delivery_age": interval[0] if interval and interval[0] == interval[1] else None,
                         "delivery_age_interval": interval, "clock_status": "COMPARABLE" if ordered else "HOLD_UNORDERED_LINEAGE"})

    effect = row["effect"]
    relevant = bool(effect and effect["relevant"] is True and effect["opportunity_id"] == row.get("opportunity_id", row["id"].replace("_", "-")))
    if not row["eligible"] or not row["needs_intervention"]:
        outcome = "NOT_APPLICABLE"
    elif relevant and (not comparable or effect["clock_ordered"] is not True):
        outcome = "UNKNOWN_CLOCK_RELATION"
    elif relevant and limits(effect, "time", "time_interval")[1] <= row["deadline"]:
        outcome = "RELEVANT_EFFECT_ON_TIME"
    elif relevant and limits(effect, "time", "time_interval")[0] > row["deadline"]:
        outcome = "RELEVANT_EFFECT_LATE"
    elif relevant:
        outcome = "UNKNOWN_CLOCK_RELATION"
    elif row["end_time"] >= row["deadline"]:
        outcome = "MISSED_NO_RELEVANT_EFFECT"
    else:
        outcome = "UNKNOWN_NO_RELEVANT_EFFECT"

    age, age_interval, status = None, None, "NO_RELEVANT_EFFECT"
    if not row["eligible"] or not row["needs_intervention"]:
        status = "NOT_APPLICABLE"
    elif relevant:
        if not comparable or effect["clock_ordered"] is not True:
            status = "HOLD_UNORDERED_LINEAGE"
        elif effect["lineage_proven"] is not True or len(effect["lineage"]) != 1:
            status = "HOLD_CAUSAL_ANCESTOR_UNKNOWN"
        else:
            source = next((o for o in row["observations"] if o["id"] == effect["lineage"][0]), None)
            if source is None:
                status = "HOLD_LINEAGE_SOURCE_MISSING"
            else:
                g0, g1 = limits(source, "generation", "generation_interval")
                e0, e1 = limits(effect, "time", "time_interval")
                if g1 >= e0:
                    status = "HOLD_UNORDERED_LINEAGE"
                else:
                    status = "SINGLE_PROVEN_SOURCE"
                    age_interval = [e0 - g1, e1 - g0]
                    if age_interval[0] == age_interval[1]:
                        age = age_interval[0]

    source = next((o for o in row["observations"] if relevant and status == "SINGLE_PROVEN_SOURCE" and o["id"] == effect["lineage"][0]), None)
    onset_interval = None
    onset_scalar = None
    if relevant and comparable and row["onset"] is not None:
        e0, e1 = limits(effect, "time", "time_interval")
        if row["onset"] < e0:
            onset_interval = [e0 - row["onset"], e1 - row["onset"]]
            if onset_interval[0] == onset_interval[1]:
                onset_scalar = onset_interval[0]
    return {"events": row, "id": row["id"], "delivery_ages": delivery,
            "opportunity_outcome": outcome, "onset_to_effect": onset_scalar,
            "onset_to_effect_interval": onset_interval, "source_effect_age": age,
            "source_effect_age_interval": age_interval, "source_effect_age_status": status,
            "source_validity": source["validity"] if source else None,
            "relevant_effect_reset": relevant}


def run(fixture):
    return [derive({**row, "end_time": fixture["end_time"]}) for row in fixture["rows"]]

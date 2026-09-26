"""Frozen composition predicates for the model-facing v2 first unit."""
POLICIES = (
    "TYPED_EPOCH_AWARE_COMPOSER",
    "LATEST_CHANNEL_WINS",
    "BEST_EFFORT_MERGE",
    "EPOCH_REJECT_ONLY",
)


def records(scenario):
    return [{"channel": "image", **scenario["image"]}, *scenario["channels"]]


def compose(scenario, policy, max_skew_ms):
    rows = records(scenario)
    epochs = {r["epoch"] for r in rows}
    task_ids = {r["task_id"] for r in rows}
    capture = [r["capture_ms"] for r in rows]
    skew = max(capture) - min(capture)
    duplicate_channels = len({r["channel"] for r in rows}) != len(rows)
    if policy == "TYPED_EPOCH_AWARE_COMPOSER":
        if len(epochs) != 1 or len(task_ids) != 1 or duplicate_channels or skew > max_skew_ms:
            return {"disposition": "ABSTAIN_BEFORE_MODEL", "bundle": [], "authority": False}
        return {"disposition": "COMPOSE_SKEWED_CONTEXT" if skew else "COMPOSE_COHERENT",
                "bundle": rows, "authority": False}
    if policy == "EPOCH_REJECT_ONLY":
        if len(epochs) != 1 or len(task_ids) != 1 or duplicate_channels or skew != 0:
            return {"disposition": "ABSTAIN_BEFORE_MODEL", "bundle": [], "authority": False}
        return {"disposition": "COMPOSE_COHERENT", "bundle": rows, "authority": False}
    if policy == "LATEST_CHANNEL_WINS":
        latest = {}
        for row in rows:
            previous = latest.get(row["channel"])
            if previous is None or row["arrival_ms"] > previous["arrival_ms"]:
                latest[row["channel"]] = row
        return {"disposition": "COMPOSE_LATEST_PER_CHANNEL",
                "bundle": list(latest.values()), "authority": False}
    if policy == "BEST_EFFORT_MERGE":
        return {"disposition": "COMPOSE_ALL_AVAILABLE",
                "bundle": rows, "authority": False}
    raise ValueError("unknown policy")

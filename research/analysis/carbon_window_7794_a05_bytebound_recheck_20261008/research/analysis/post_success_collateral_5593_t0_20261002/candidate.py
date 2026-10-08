TERMINAL = {"verified_success", "verified_failure", "policy_safe_stop"}
EVENT_TYPES = TERMINAL | {"collateral_observed", "followup_complete", "followup_lost"}


def _events(episode):
    events = episode.get("events")
    if not isinstance(episode.get("id"), str) or not episode["id"]:
        raise ValueError("episode requires a nonempty id")
    if type(episode.get("launch")) is not int or episode["launch"] < 0:
        raise ValueError("episode launch must be a nonnegative integer")
    if not isinstance(events, list) or not events:
        raise ValueError("episode requires events")
    previous_time = episode["launch"]
    terminals = []
    losses = 0
    completes = 0
    for row in events:
        if not isinstance(row, dict) or row.get("type") not in EVENT_TYPES:
            raise ValueError("unknown event type")
        time = row.get("time")
        if type(time) is not int or time < previous_time:
            raise ValueError("event times must be ordered nonnegative integers")
        previous_time = time
        if row["type"] in TERMINAL:
            terminals.append(row)
        losses += row["type"] == "followup_lost"
        completes += row["type"] == "followup_complete"
    if len(terminals) > 1 or losses > 1 or completes > 1 or (losses and completes):
        raise ValueError("duplicate or conflicting terminal/followup event")
    return events, terminals[0] if terminals else None


def evaluate_episode(episode, horizons):
    events, terminal = _events(episode)
    success = terminal if terminal and terminal["type"] == "verified_success" else None
    result = {
        "episode_id": episode["id"],
        "first_terminal_type": terminal["type"] if terminal else None,
        "first_terminal_time": terminal["time"] if terminal else None,
        "horizons": {},
    }
    for horizon in horizons:
        cutoff = episode["launch"] + horizon
        collateral = any(e["type"] == "collateral_observed" and e["time"] <= cutoff
                         for e in events)
        if collateral:
            status = "COLLATERAL_OBSERVED"
        elif not success or success["time"] > cutoff:
            status = "NO_VERIFIED_SUCCESS_BY_HORIZON"
        else:
            complete = (any(e["type"] == "followup_complete" and e["time"] >= cutoff
                            for e in events)
                        or any(e["type"] == "followup_lost" and e["time"] > cutoff
                               for e in events))
            lost = any(e["type"] == "followup_lost" and e["time"] <= cutoff
                       for e in events)
            if complete:
                status = "NO_COLLATERAL_COMPLETE"
            elif lost:
                status = "FOLLOWUP_UNKNOWN"
            else:
                status = "FOLLOWUP_PENDING"
        result["horizons"][str(horizon)] = {"cutoff": cutoff, "status": status}
    return result


def summarize(cohort, horizons):
    if not isinstance(cohort, list) or not cohort:
        raise ValueError("cohort must be nonempty")
    if (not isinstance(horizons, list) or not horizons
            or any(type(h) is not int or h <= 0 for h in horizons)
            or sorted(set(horizons)) != horizons):
        raise ValueError("horizons must be unique increasing positive integers")
    ids = [episode.get("id") for episode in cohort]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate episode id")
    task_contracts = {episode.get("task_contract") for episode in cohort}
    if len(task_contracts) != 1 or None in task_contracts:
        raise ValueError("cohort must have one frozen task contract")
    rows = [evaluate_episode(episode, horizons) for episode in cohort]
    terminal_counts = {kind: sum(row["first_terminal_type"] == kind for row in rows)
                       for kind in sorted(TERMINAL)}
    n = len(rows)
    horizon_results = {}
    for horizon in horizons:
        states = [row["horizons"][str(horizon)]["status"] for row in rows]
        clean_n = states.count("NO_COLLATERAL_COMPLETE")
        uncertain_n = states.count("FOLLOWUP_UNKNOWN") + states.count("FOLLOWUP_PENDING")
        horizon_results[str(horizon)] = {
            "cutoff_from_launch": horizon,
            "states": {state: states.count(state) for state in sorted(set(states))},
            "all_launched_n": n,
            "clean_lower_n": clean_n,
            "clean_upper_n": clean_n + uncertain_n,
            "clean_lower_fraction": clean_n / n,
            "clean_upper_fraction": (clean_n + uncertain_n) / n,
        }
    success_n = terminal_counts["verified_success"]
    return {
        "schema": "post-success-collateral-candidate-v1",
        "all_launched_n": n,
        "first_terminal_counts": terminal_counts,
        "first_terminal_success_n": success_n,
        "first_terminal_success_fraction": success_n / n,
        "horizons": horizon_results,
        "episodes": rows,
    }

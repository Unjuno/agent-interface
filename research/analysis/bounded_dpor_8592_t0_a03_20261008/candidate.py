"""Small deterministic sleep-set DPOR schedule enumerator."""

from math import factorial


def initial_state():
    return {
        "task_generation": 1,
        "observation_generation": 1,
        "lease_open": True,
        "authority_epoch": 1,
        "cancelled": False,
        "dispatch_accepted": False,
        "physical_release": False,
        "effect_receipt": False,
        "acknowledged": False,
        "diagnostic_markers": [],
        "violations": [],
    }


def apply_event(state, event):
    next_state = {**state, "violations": list(state["violations"])}
    kind = event["kind"]
    status = "applied"
    if kind == "observation_update":
        next_state["observation_generation"] += 1
        status = "updated"
    elif kind == "lease_revoke":
        next_state["lease_open"] = False
        next_state["authority_epoch"] += 1
        status = "revoked"
    elif kind == "cancel":
        next_state["cancelled"] = True
        status = "cancelled"
    elif kind == "dispatch":
        if not next_state["lease_open"] or next_state["cancelled"]:
            status = "blocked_authority_or_cancel"
        elif next_state["observation_generation"] != next_state["task_generation"]:
            status = "blocked_stale_generation"
        else:
            next_state["dispatch_accepted"] = True
            status = "accepted"
    elif kind == "release":
        if not next_state["dispatch_accepted"]:
            status = "blocked_no_dispatch"
        elif not next_state["lease_open"]:
            status = "blocked_revoked_authority"
        elif next_state["observation_generation"] != next_state["task_generation"]:
            status = "blocked_stale_generation"
        else:
            next_state["physical_release"] = True
            status = "released"
    elif kind == "effect_receipt":
        if next_state["physical_release"]:
            next_state["effect_receipt"] = True
            status = "verified_effect"
        else:
            status = "unknown_no_release_receipt"
    elif kind == "acknowledgement":
        if next_state["effect_receipt"]:
            next_state["acknowledged"] = True
            status = "acknowledged"
        else:
            next_state["violations"].append("ACK_BEFORE_EFFECT_RECEIPT")
            status = "violation_ack_without_receipt"
    elif kind == "diagnostic_marker":
        next_state["diagnostic_markers"] = sorted((*next_state["diagnostic_markers"], event["id"]))
        status = "marker_recorded"
    else:
        raise ValueError(f"unknown event kind: {kind}")
    return next_state, {"event_id": event["id"], "kind": kind, "status": status}


def derive_independent_pairs(events):
    required = ("reads", "writes", "guards", "enables", "effects", "authority_epoch")
    footprints = {}
    for event in events:
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id or event_id in footprints:
            raise ValueError("event ids must be unique non-empty strings")
        if event.get("unknown_dependency"):
            footprints[event_id] = None
            continue
        if any(key not in event or not isinstance(event[key], list) for key in required):
            footprints[event_id] = None
            continue
        footprint = set()
        for key in required:
            footprint.update(event[key])
        footprints[event_id] = footprint
    independent = set()
    ids = sorted(footprints)
    for index, left in enumerate(ids):
        for right in ids[index + 1 :]:
            left_footprint, right_footprint = footprints[left], footprints[right]
            if left_footprint is not None and right_footprint is not None and left_footprint.isdisjoint(right_footprint):
                independent.add(frozenset((left, right)))
    return independent


def run(data):
    if data.get("schema") != "bounded-dpor-input-v1" or not isinstance(data.get("cases"), list):
        raise ValueError("unsupported frozen input")
    cases = []
    for case in data["cases"]:
        events = tuple(case["events"])
        ids = tuple(event["id"] for event in events)
        independent = derive_independent_pairs(events)
        schedules, stats = reduced_schedules(ids, independent)
        traces = []
        for index, schedule in enumerate(schedules):
            state = initial_state()
            outputs = []
            event_by_id = {event["id"]: event for event in events}
            for event_id in schedule:
                state, output = apply_event(state, event_by_id[event_id])
                outputs.append(output)
            traces.append({
                "schedule_id": f"{case['case_id']}:{index:04d}",
                "order": list(schedule),
                "outputs": outputs,
                "final_state": state,
                "violations": list(state["violations"]),
            })
        pair_traces = []
        for left in ids:
            for right in ids:
                if left == right:
                    continue
                state = initial_state()
                outputs = []
                for event_id in (left, right):
                    state, output = apply_event(state, event_by_id[event_id])
                    outputs.append(output)
                pair_traces.append({
                    "order": [left, right],
                    "outputs": outputs,
                    "final_state": state,
                })
        pairs = [sorted(pair) for pair in sorted(independent, key=lambda item: sorted(item))]
        cases.append({
            "case_id": case["case_id"],
            "event_ids": list(ids),
            "independent_pairs": pairs,
            "full_schedule_count": factorial(len(ids)),
            "reduced_schedule_count": stats["terminal_schedules"],
            "sleep_pruned_prefixes": stats["sleep_pruned_prefixes"],
            "schedule_traces": traces,
            "ordered_pair_baseline": {
                "trace_count": len(pair_traces),
                "ordered_pairs": [[trace["order"][0], trace["order"][1]] for trace in pair_traces],
                "pair_traces": pair_traces,
            },
        })
    return {"schema": "bounded-dpor-candidate-v1", "cases": cases}


def reduced_schedules(events, independent_pairs):
    events = tuple(events)
    if len(events) != len(set(events)) or any(not isinstance(event, str) or not event for event in events):
        raise ValueError("events must be unique non-empty strings")
    normalized = set()
    for pair in independent_pairs:
        pair = frozenset(pair)
        if len(pair) != 2 or not pair <= set(events):
            raise ValueError("independence pairs must name two distinct frozen events")
        normalized.add(pair)

    schedules = []
    pruned = 0

    def visit(prefix, remaining, sleep):
        nonlocal pruned
        if not remaining:
            schedules.append(tuple(prefix))
            return
        local_sleep = set(sleep)
        for event in sorted(remaining):
            if event in local_sleep:
                pruned += 1
                continue
            child_sleep = {prior for prior in local_sleep if frozenset((prior, event)) in normalized}
            visit((*prefix, event), remaining - {event}, child_sleep)
            local_sleep.add(event)

    visit((), set(events), set())
    return tuple(schedules), {
        "terminal_schedules": len(schedules),
        "sleep_pruned_prefixes": pruned,
    }

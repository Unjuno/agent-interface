import json
import sys

ALLOWED = {
    "RUNNING": {"SAFE_STOP", "VERIFIED_SUCCESS", "VERIFIED_FAILURE", "ADMIN_CENSOR"},
    "SAFE_STOP": {"RECOVERING", "TERMINAL_STOP"},
    "RECOVERING": {"SAFE_STOP", "VERIFIED_SUCCESS", "VERIFIED_FAILURE", "TERMINAL_STOP", "ADMIN_CENSOR"},
    "VERIFIED_SUCCESS": set(), "VERIFIED_FAILURE": set(), "TERMINAL_STOP": set(),
    "ADMIN_CENSOR": set(),
}


def reconstruct(data):
    episodes = data["episodes"]
    ids = [ep["id"] for ep in episodes]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate episode id")
    for ep in episodes:
        events = ep["events"]
        if not events or events[0] != {"tick": 0, "state": "RUNNING"}:
            raise ValueError("episode must launch once at tick 0")
        previous_tick = -1
        previous_state = None
        for event in events:
            tick, state = event["tick"], event["state"]
            if not isinstance(tick, int) or tick < 0 or tick <= previous_tick:
                raise ValueError("invalid event clock")
            if state not in ALLOWED:
                raise ValueError("unknown event/status")
            if previous_state is not None and state not in ALLOWED[previous_state]:
                raise ValueError(f"illegal transition {previous_state}->{state}")
            previous_tick, previous_state = tick, state
    last_tick = max(event["tick"] for ep in episodes for event in ep["events"])
    occupancy, transitions = [], []
    for tick in range(last_tick + 1):
        occ, trans = {}, {}
        for ep in episodes:
            events = ep["events"]
            active = [event for event in events if event["tick"] <= tick]
            state = active[-1]["state"]
            if state == "ADMIN_CENSOR":
                state = "CENSORED"
            occ[state] = occ.get(state, 0) + 1
            for previous, current in zip(events, events[1:]):
                if current["tick"] == tick:
                    key = f"{previous['state']}->{current['state']}"
                    trans[key] = trans.get(key, 0) + 1
        occupancy.append({"tick": tick, "counts": dict(sorted(occ.items()))})
        transitions.append({"tick": tick, "counts": dict(sorted(trans.items()))})
        if sum(occ.values()) != len(episodes):
            raise ValueError("launched denominator mass lost")
    return {"allocation": data["allocation"], "launched_n": len(episodes), "occupancy": occupancy, "transitions": transitions}


def audit(data, observed):
    expected = reconstruct(data)
    if observed != expected:
        raise ValueError("candidate output differs from independent raw-ledger reconstruction")
    controls = []
    mutations = []
    omitted = json.loads(json.dumps(data))
    omitted["episodes"].pop()
    mutations.append(("omitted_episode", omitted, None))
    recovery = json.loads(json.dumps(data))
    recovery["episodes"][0]["events"].pop(2)
    mutations.append(("omitted_recovery", recovery, None))
    absorbing = json.loads(json.dumps(data))
    absorbing["episodes"][0]["events"].append({"tick": 5, "state": "RECOVERING"})
    mutations.append(("illegal_after_absorbing", absorbing, None))
    unknown = json.loads(json.dumps(data))
    unknown["episodes"][1]["events"][2]["state"] = "TERMINAL_MAYBE"
    mutations.append(("unknown_status", unknown, None))
    duplicate = json.loads(json.dumps(data))
    duplicate["episodes"][1]["id"] = duplicate["episodes"][0]["id"]
    mutations.append(("duplicate_id", duplicate, None))
    wrong_denominator = json.loads(json.dumps(observed))
    wrong_denominator["launched_n"] -= 1
    mutations.append(("denominator_loss", data, wrong_denominator))
    for name, mutated_data, mutated_output in mutations:
        rejected = False
        try:
            if mutated_output is None:
                reconstruct(mutated_data)
            else:
                audit(mutated_data, mutated_output)
        except (ValueError, KeyError, IndexError):
            rejected = True
        if not rejected:
            raise ValueError(f"mutation not rejected: {name}")
        controls.append(name)
    return {"disposition": "PASS_METHOD_MULTISTATE_SCOPED", "episodes": expected["launched_n"], "ticks": len(expected["occupancy"]), "errors": [], "mutation_controls_rejected": controls}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        raw = json.load(handle)
    with open(sys.argv[2], encoding="utf-8") as handle:
        observed = json.load(handle)
    result = audit(raw, observed)
    with open(sys.argv[3], "w", encoding="utf-8") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps(result, sort_keys=True))

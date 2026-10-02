import json
import sys

ALLOWED = {
    "RUNNING": {"SAFE_STOP", "VERIFIED_SUCCESS", "VERIFIED_FAILURE", "ADMIN_CENSOR"},
    "SAFE_STOP": {"RECOVERING", "TERMINAL_STOP"},
    "RECOVERING": {"SAFE_STOP", "VERIFIED_SUCCESS", "VERIFIED_FAILURE", "TERMINAL_STOP", "ADMIN_CENSOR"},
    "VERIFIED_SUCCESS": set(), "VERIFIED_FAILURE": set(), "TERMINAL_STOP": set(), "ADMIN_CENSOR": set(),
}


def reconstruct(data, roster):
    ids = [ep["id"] for ep in data["episodes"]]
    if roster["allocation"] != data["allocation"]:
        raise ValueError("allocation mismatch")
    if len(ids) != roster["launched_n"] or sorted(ids) != sorted(roster["episode_ids"]) or len(ids) != len(set(ids)):
        raise ValueError("frozen launch roster mismatch")
    for ep in data["episodes"]:
        events = ep["events"]
        if not events or events[0] != {"tick": 0, "state": "RUNNING"}:
            raise ValueError("episode must launch once at tick 0")
        prev_tick, prev_state = -1, None
        for event in events:
            tick, state = event["tick"], event["state"]
            if not isinstance(tick, int) or tick < 0 or tick <= prev_tick:
                raise ValueError("invalid event clock")
            if state not in ALLOWED:
                raise ValueError("unknown event/status")
            if prev_state is not None and state not in ALLOWED[prev_state]:
                raise ValueError(f"illegal transition {prev_state}->{state}")
            prev_tick, prev_state = tick, state
    last_tick = max(event["tick"] for ep in data["episodes"] for event in ep["events"])
    occupancy, transitions = [], []
    for tick in range(last_tick + 1):
        occ, trans = {}, {}
        for ep in data["episodes"]:
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
        if sum(occ.values()) != roster["launched_n"]:
            raise ValueError("denominator mass lost")
        occupancy.append({"tick": tick, "counts": dict(sorted(occ.items()))})
        transitions.append({"tick": tick, "counts": dict(sorted(trans.items()))})
    return {"allocation": data["allocation"], "launched_n": roster["launched_n"], "episode_ids": sorted(ids), "occupancy": occupancy, "transitions": transitions}


def audit(data, roster, observed):
    expected = reconstruct(data, roster)
    if observed != expected:
        raise ValueError("candidate output differs from frozen-roster reconstruction")
    controls = []
    omitted = json.loads(json.dumps(data)); omitted["episodes"].pop()
    bad_recovery = json.loads(json.dumps(data)); bad_recovery["episodes"][0]["events"].pop(2)
    after_absorbing = json.loads(json.dumps(data)); after_absorbing["episodes"][0]["events"].append({"tick": 5, "state": "RECOVERING"})
    unknown = json.loads(json.dumps(data)); unknown["episodes"][1]["events"][2]["state"] = "TERMINAL_MAYBE"
    duplicate = json.loads(json.dumps(data)); duplicate["episodes"][1]["id"] = duplicate["episodes"][0]["id"]
    wrong_n = json.loads(json.dumps(observed)); wrong_n["launched_n"] -= 1
    mutations = [("omitted_episode", omitted, observed), ("omitted_recovery", bad_recovery, observed), ("illegal_after_absorbing", after_absorbing, observed), ("unknown_status", unknown, observed), ("duplicate_id", duplicate, observed), ("denominator_loss", data, wrong_n)]
    for name, changed_data, changed_output in mutations:
        rejected = False
        try:
            if name == "denominator_loss":
                if changed_output != reconstruct(changed_data, roster):
                    raise ValueError("denominator/output mismatch")
            else:
                reconstruct(changed_data, roster)
        except (ValueError, KeyError, IndexError):
            rejected = True
        if not rejected:
            raise ValueError(f"mutation not rejected: {name}")
        controls.append(name)
    return {"disposition": "PASS_METHOD_MULTISTATE_ROSTER_SCOPED", "episodes": roster["launched_n"], "ticks": len(expected["occupancy"]), "errors": [], "mutation_controls_rejected": controls}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f: raw = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f: roster = json.load(f)
    with open(sys.argv[3], encoding="utf-8") as f: observed = json.load(f)
    result = audit(raw, roster, observed)
    with open(sys.argv[4], "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, indent=2); f.write("\n")
    print(json.dumps(result, sort_keys=True))

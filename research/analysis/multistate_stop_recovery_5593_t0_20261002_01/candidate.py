import json
import sys


def derive(data):
    episodes = data["episodes"]
    last_tick = max(event["tick"] for ep in episodes for event in ep["events"])
    occupancy = []
    transitions = []
    for tick in range(last_tick + 1):
        counts = {}
        trans = {}
        for ep in episodes:
            events = ep["events"]
            active = [event for event in events if event["tick"] <= tick]
            state = active[-1]["state"]
            if state == "ADMIN_CENSOR":
                state = "CENSORED"
            counts[state] = counts.get(state, 0) + 1
            if tick > 0:
                for previous, event in zip(events, events[1:]):
                    if event["tick"] == tick:
                        key = f"{previous['state']}->{event['state']}"
                        trans[key] = trans.get(key, 0) + 1
        occupancy.append({"tick": tick, "counts": dict(sorted(counts.items()))})
        transitions.append({"tick": tick, "counts": dict(sorted(trans.items()))})
    return {"allocation": data["allocation"], "launched_n": len(episodes), "occupancy": occupancy, "transitions": transitions}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        result = derive(json.load(handle))
    with open(sys.argv[2], "w", encoding="utf-8") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({"allocation": result["allocation"], "launched_n": result["launched_n"], "ticks": len(result["occupancy"])}))

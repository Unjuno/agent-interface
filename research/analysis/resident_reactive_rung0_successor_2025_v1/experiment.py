import hashlib, json
from itertools import product

# Finite Rung 0 oracle: one declared rising edge, planner unavailable in [1,3).
# Event traces are binary predicate states at t=0..3; deadline is t=4.
def resident(trace, generation_message):
    fired = 0
    owned = True
    prev = False
    events = []
    generation = 1
    for t, state in enumerate(trace):
        if generation_message == (t, 0):  # stale steering must be rejected
            pass
        if state and not prev and owned:
            fired += 1
            events.append(("effect", t, generation))
        prev = state
    owned = False  # deadline/revoke release
    events.append(("release", 4, generation))
    return events, fired, owned

def poll(trace):
    # External polling waits for planner return at t=3, then observes at t=3.
    return [("effect", 3, 1)] if any(trace[1:3]) else []

def open_loop(trace):
    # Fixed macro attempts once at t=1 regardless of predicate.
    return [("effect", 1, 1)]

def main():
    rows=[]
    for trace in product((False, True), repeat=4):
        for msg_t in range(4):
            events, fired, owned = resident(trace, (msg_t, 0))
            valid = sum(1 for e in events if e[0]=="effect") == sum(
                1 for i,s in enumerate(trace) if s and (i==0 or not trace[i-1])
            ) and not owned and events[-1][0]=="release"
            rows.append({"trace":trace,"msg_t":msg_t,"resident":events,
                         "poll":poll(trace),"open_loop":open_loop(trace),"valid":valid})
    raw=json.dumps(rows,sort_keys=True,separators=(",",":"))
    print(json.dumps({"rows":len(rows),"valid":sum(r["valid"] for r in rows),
      "resident_edges":sum(sum(e[0]=="effect" for e in r["resident"]) for r in rows),
      "poll_responses_during_delay":sum(bool(r["poll"]) for r in rows),
      "open_loop_false_positive":sum(bool(r["open_loop"]) and not any(r["trace"][1:3]) for r in rows),
      "sha256":hashlib.sha256(raw.encode()).hexdigest()}))
if __name__=="__main__": main()

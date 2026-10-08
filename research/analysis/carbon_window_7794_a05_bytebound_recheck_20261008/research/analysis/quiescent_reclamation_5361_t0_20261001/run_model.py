import collections
import hashlib
import json
import pathlib
import platform
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
EVENTS = ("A0", "A1", "R", "U0", "U1", "Q0", "Q1", "Q0_STALE", "F")
NAMES = ("NEVER", "ACTIVE", "QUIESCENT", "FENCED")
START = (0, 0, False)  # reader-0 state, reader-1 state, removed


def step(state, event):
    a, b, removed = state
    readers = [a, b]
    if event in ("A0", "A1"):
        i = int(event[1])
        if not removed and readers[i] == 0:
            readers[i] = 1
    elif event == "R":
        removed = True
    elif event in ("Q0", "Q1"):
        i = int(event[1])
        if readers[i] == 1:
            readers[i] = 2
    elif event == "Q0_STALE":
        pass  # stale generation receipt never changes a current reader
    elif event == "F":
        readers = [3 if x == 1 else x for x in readers]
    elif event in ("U0", "U1"):
        pass  # use is recorded as an observation, not a state mutation
    return (readers[0], readers[1], removed)


def reclaimed(state):
    return state[2] and 1 not in state[:2]


def use_allowed(state, reader):
    # Admission is checked at use time; a reader may continue only while ACTIVE.
    if reclaimed(state):
        return False
    return state[reader] == 1


def explore():
    # State graph carries the shortest representative event history per state.
    q = collections.deque([START])
    paths = {START: ()}
    edges = 0
    baseline_witness = None
    bad_after_reclaim = []
    two_phase_after_remove = 0
    baseline_after_declared_reclaim = 0
    stale_accepted = 0
    while q:
        state = q.popleft()
        path = paths[state]
        for event in EVENTS:
            edges += 1
            prior_removed = state[2]
            prior_reclaimed = reclaimed(state)
            if event in ("U0", "U1"):
                reader_index = int(event[1])
                reader = state[reader_index]
                if reader == 1 and prior_removed and baseline_witness is None:
                    baseline_witness = list(path + (event,))
                if prior_removed and use_allowed(state, reader_index):
                    two_phase_after_remove += 1
                if prior_reclaimed and use_allowed(state, reader_index):
                    bad_after_reclaim.append(list(path + (event,)))
                if prior_removed and reader == 1:
                    # Revoke-only baseline calls REMOVE reclaimed immediately,
                    # yet its old-reader gate still accepts this action.
                    baseline_after_declared_reclaim += 1
            nxt = step(state, event)
            if event == "Q0_STALE" and nxt != state:
                stale_accepted += 1
            if nxt not in paths:
                paths[nxt] = path + (event,)
                q.append(nxt)
    # The issue's revoke-only policy marks REMOVE as reclaimed immediately.
    baseline = None
    for state, path in paths.items():
        if state[2] and state[0] == 1:
            for event in EVENTS:
                if event == "U0":
                    baseline = list(path + (event,))
                    break
            if baseline:
                break
    return {
        "event_alphabet": list(EVENTS),
        "reader_state_names": list(NAMES),
        "reachable_state_count": len(paths),
        "transition_count": edges,
        "baseline_remove_then_active_use_witness": baseline,
        "two_phase_reclaim_then_active_use_witnesses": bad_after_reclaim,
        "two_phase_allowed_uses_after_remove": two_phase_after_remove,
        "baseline_allowed_uses_after_declared_reclaim": baseline_after_declared_reclaim,
        "stale_receipt_state_changes": stale_accepted,
        "reclaimed_states_with_active_reader": sum(
            reclaimed(s) and 1 in s[:2] for s in paths
        ),
        "terminal_state_inventory": [
            {"readers": [NAMES[s[0]], NAMES[s[1]]], "removed": s[2],
             "reclaimed": reclaimed(s)}
            for s in sorted(paths)
        ],
        "shortest_paths": [
            {"state": list(s), "events": list(paths[s])}
            for s in sorted(paths)
        ],
    }


def main():
    out = HERE / "candidate_raw.json"
    if out.exists():
        raise SystemExit("REFUSE_OVERWRITE candidate_raw.json")
    start = time.perf_counter_ns()
    graph = explore()
    graph["environment"] = {
        "python": sys.version,
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "elapsed_ns": time.perf_counter_ns() - start,
    }
    payload = json.dumps(graph, sort_keys=True, indent=2) + "\n"
    out.write_text(payload, encoding="utf-8", newline="\n")
    print(json.dumps({
        "candidate": "COMPLETE",
        "raw_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "reachable_state_count": graph["reachable_state_count"],
        "transition_count": graph["transition_count"],
        "baseline_witness": graph["baseline_remove_then_active_use_witness"],
        "two_phase_unsafe_witness_count": len(graph["two_phase_reclaim_then_active_use_witnesses"]),
        "stale_receipt_state_changes": graph["stale_receipt_state_changes"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()

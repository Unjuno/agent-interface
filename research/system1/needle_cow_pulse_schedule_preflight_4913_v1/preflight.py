"""Zero-optimizer construction check for Issue #4913 pulse scheduling."""
import json
from queue import Queue

ARRIVALS = 12
STEPS = 16
PULSE_QUERIES = tuple(range(0, 120, 10))


def apply(state, arrival, step):
    # Integer surrogate for immutable per-update state; no model/optimizer work.
    return state * 131 + arrival * 17 + step + 1


def continuous():
    state = 0
    publications = [state]
    for arrival in range(ARRIVALS):
        for step in range(STEPS):
            state = apply(state, arrival, step)
        publications.append(state)
    return publications


def pulsed():
    state = 0
    publications = [state]
    pending = Queue()
    active = 0
    max_active = 0
    for pulse, query_index in enumerate(PULSE_QUERIES):
        if query_index != pulse * 10:
            raise AssertionError("pulse boundary")
        active += 1
        max_active = max(max_active, active)
        for step in range(STEPS):
            state = apply(state, pulse, step)
        pending.put((pulse + 1, state))
        active -= 1
        version, published_state = pending.get_nowait()
        if version != len(publications):
            raise AssertionError("publication order")
        publications.append(published_state)
    return publications, max_active


def main():
    reference = continuous()
    candidate, max_active = pulsed()
    result = {
        "classification": "CONSTRUCTION_ONLY_PASS" if candidate == reference and len(candidate) == 13 and max_active == 1 else "CONSTRUCTION_FAIL",
        "formal_optimizer_steps": 0,
        "formal_seeds_used": [],
        "total_schedule_slots": ARRIVALS * STEPS,
        "publication_versions_including_initial": len(candidate),
        "per_publication_state_equal": candidate == reference,
        "pulse_boundaries": list(PULSE_QUERIES),
        "max_concurrent_workers": max_active,
        "query_deadline_measurements": 0,
        "scope": "integer schedule surrogate only; not COW, AdamW, timing, or model evidence",
    }
    print(json.dumps(result, sort_keys=True))
    if result["classification"] != "CONSTRUCTION_ONLY_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Zero-optimizer construction check for Issue #4913 pulse scheduling."""
import json
import threading
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
    completed = Queue()
    active = {"count": 0, "max": 0}
    guard = threading.Lock()
    for pulse, query_index in enumerate(PULSE_QUERIES):
        if query_index != pulse * 10:
            raise AssertionError("pulse boundary")

        def work(arrival=pulse, initial=state):
            with guard:
                active["count"] += 1
                active["max"] = max(active["max"], active["count"])
            result = initial
            for step in range(STEPS):
                result = apply(result, arrival, step)
            with guard:
                active["count"] -= 1
            completed.put((arrival + 1, result))

        worker = threading.Thread(target=work, name=f"pulse-{pulse}")
        worker.start()
        version, published_state = completed.get(timeout=5)
        worker.join(timeout=5)
        if worker.is_alive():
            raise AssertionError("pulse worker did not join before next boundary")
        if active["count"] != 0:
            raise AssertionError("worker remained active at publication")
        if version != len(publications):
            raise AssertionError("publication order")
        state = published_state
        publications.append(published_state)
    return publications, active["max"]


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
        "scope": "threaded integer schedule surrogate only; not COW, AdamW, timing, or model evidence",
    }
    print(json.dumps(result, sort_keys=True))
    if result["classification"] != "CONSTRUCTION_ONLY_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

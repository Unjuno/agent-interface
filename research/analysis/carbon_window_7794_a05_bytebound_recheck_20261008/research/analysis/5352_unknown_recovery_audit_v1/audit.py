"""Independent exhaustive audit; intentionally does not import enumerate.py."""
from itertools import product

ALPHABET = (0.64, 0.65, 0.66, 0.69, 0.70, 0.71, "STALE", "CRITICAL")
MAX_LENGTH = 6


def independently_step(state, item):
    # Critical evidence has hard priority. A stale sample invalidates mode.
    if item == "CRITICAL":
        return "ESCALATED"
    if item == "STALE":
        return "UNKNOWN"
    # UNKNOWN has no rebootstrap rule in the current literal specification.
    if state == "UNKNOWN":
        return "UNKNOWN"
    # Hysteresis band: enter at .70; leave at .65.
    if state == "ESCALATED":
        return "LOCAL" if item <= 0.65 else "ESCALATED"
    return "ESCALATED" if item >= 0.70 else "LOCAL"


def path(trace):
    state = "LOCAL"
    states = []
    for item in trace:
        state = independently_step(state, item)
        states.append(state)
    return states


def main():
    traces = 0
    transition_cases = 0
    first_valid_cases = 0
    first_valid_stuck = 0
    subsequent_valid_rows = 0
    critical_events = 0
    critical_same_step = 0
    first_transition_failure = None
    first_critical_failure = None
    for length in range(1, MAX_LENGTH + 1):
        for trace in product(ALPHABET, repeat=length):
            traces += 1
            states = path(trace)
            for i, item in enumerate(trace):
                if item == "CRITICAL":
                    critical_events += 1
                    if states[i] == "ESCALATED":
                        critical_same_step += 1
                    elif first_critical_failure is None:
                        first_critical_failure = {"trace": trace, "states": states, "index": i}
                if item == "STALE":
                    later_valid = next((j for j in range(i + 1, len(trace))
                                        if isinstance(trace[j], float)), None)
                    if later_valid is not None:
                        transition_cases += 1
                        first_valid_cases += 1
                        if states[later_valid] == "UNKNOWN":
                            first_valid_stuck += 1
                        elif first_transition_failure is None:
                            first_transition_failure = {
                                "trace": trace, "states": states,
                                "stale_index": i, "valid_index": later_valid,
                            }
                        subsequent_valid_rows += sum(
                            isinstance(value, float) and states[j] == "UNKNOWN"
                            for j, value in enumerate(trace[i + 1:], start=i + 1)
                        )
    print({
        "alphabet_size": len(ALPHABET),
        "max_length": MAX_LENGTH,
        "all_traces": traces,
        "traces_with_stale_then_valid": transition_cases,
        "stale_to_first_valid_cases": first_valid_cases,
        "stale_to_first_valid_still_unknown": first_valid_stuck,
        "later_valid_rows_still_unknown": subsequent_valid_rows,
        "first_valid_escalation_counterexample": first_transition_failure,
        "critical_events": critical_events,
        "critical_same_step_escalations": critical_same_step,
        "first_critical_failure": first_critical_failure,
    })


if __name__ == "__main__":
    main()

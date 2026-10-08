"""Small independent enumerator for the literal #5352 T0 policy description."""
from itertools import product

ALPHABET = (0.64, 0.65, 0.66, 0.69, 0.70, 0.71, "STALE", "CRITICAL")
MAX_LENGTH = 6


def step(state, item):
    if item == "CRITICAL":
        return "ESCALATED"
    if item == "STALE":
        return "UNKNOWN"
    if state == "ESCALATED":
        return "LOCAL" if item <= 0.65 else "ESCALATED"
    if item >= 0.70:
        return "ESCALATED"
    if state == "UNKNOWN":
        return "UNKNOWN"
    return "LOCAL"


def main():
    examined = 0
    critical_failures = 0
    unknown_stuck = 0
    first_critical_failure = None
    first_unknown_stuck = None
    for length in range(1, MAX_LENGTH + 1):
        for trace in product(ALPHABET, repeat=length):
            examined += 1
            state = "LOCAL"
            states = []
            critical_steps = []
            for index, item in enumerate(trace):
                state = step(state, item)
                states.append(state)
                if item == "CRITICAL":
                    critical_steps.append((index, state))
            for index, critical_state in critical_steps:
                if critical_state != "ESCALATED":
                    critical_failures += 1
                    if first_critical_failure is None:
                        first_critical_failure = (trace, states, index)
            for i, item in enumerate(trace):
                if item == "STALE":
                    j = next((j for j in range(i + 1, length)
                              if isinstance(trace[j], float)), None)
                    if j is not None:
                        if states[j] == "UNKNOWN":
                            unknown_stuck += 1
                            if first_unknown_stuck is None:
                                first_unknown_stuck = (trace, states, j)
    print({
        "alphabet": list(ALPHABET),
        "max_length": MAX_LENGTH,
        "complete_trace_count": examined,
        "critical_delay_or_suppression_cases": critical_failures,
        "stale_followed_by_valid_but_still_unknown_cases": unknown_stuck,
        "critical_override_counterexample": first_critical_failure,
        "stale_recovery_counterexample": first_unknown_stuck,
    })


if __name__ == "__main__":
    main()

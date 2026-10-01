"""Independent audit implementation for Issue #6102 T0; imports no candidate code."""
from itertools import product


def oracle_accepts(trace):
    parents = []
    for event in trace:
        if len(event) != 2:
            return False
        kind, generation = event
        if generation not in ("A", "B"):
            return False
        if kind == "open":
            parents.append(generation)
        elif kind == "close":
            if len(parents) == 0 or parents[-1] != generation:
                return False
            parents.pop()
        else:
            return False
    return len(parents) == 0


def audit():
    alphabet = ("A", "B")
    events = tuple(product(("open", "close"), alphabet))
    total = disagreements = flat_false_accepts = valid = 0
    for n in range(7):
        for trace in product(events, repeat=n):
            total += 1
            expected = oracle_accepts(trace)
            # Independently expressed bounded parent-generation FSM.
            state = ()
            fsm_known = True
            invalid = False
            for kind, generation in trace:
                if kind == "open":
                    if len(state) >= 3:
                        fsm_known = False
                        break
                    state = state + (generation,)
                elif kind == "close" and state and state[-1] == generation:
                    state = state[:-1]
                else:
                    invalid = True
                    break
            fsm = ((not invalid) and state == ()) if fsm_known else None
            # Stack result equals the independent oracle by construction here; this loop
            # audits counts and the published FSM relation, not runtime integration.
            if fsm is not None and fsm != expected:
                disagreements += 1
            flat_depth = 0
            flat_accept = True
            for kind, _ in trace:
                flat_depth += 1 if kind == "open" else -1
                if flat_depth < 0:
                    flat_accept = False
                    break
            if flat_accept and flat_depth == 0 and not expected:
                flat_false_accepts += 1
            valid += int(expected)
    return {"independent_traces": total, "valid": valid,
            "fsm_oracle_disagreements": disagreements,
            "flat_false_acceptances": flat_false_accepts}


if __name__ == "__main__":
    import json
    print(json.dumps(audit(), sort_keys=True, indent=2))

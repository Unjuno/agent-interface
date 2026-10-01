"""Finite exact T0 for Issue #6102. No GUI, model, or input is used."""
from itertools import product


def valid(trace):
    stack = []
    for op, ident in trace:
        if op == "open":
            stack.append(ident)
        elif op == "close":
            if not stack or stack[-1] != ident:
                return False
            stack.pop()
        else:
            return False
    return not stack


def flat_flag(trace):
    depth = 0
    for op, _ in trace:
        if op not in ("open", "close"):
            return False
        depth += 1 if op == "open" else -1
        if depth < 0:
            return False
    return True


def bounded_fsm(trace, max_depth=3):
    # State is the explicitly encoded bounded parent stack: an FSM on this finite alphabet.
    stack = []
    for op, ident in trace:
        if op == "open":
            if len(stack) == max_depth:
                return None
            stack.append(ident)
        elif op == "close":
            if not stack or stack[-1] != ident:
                return False
            stack.pop()
        else:
            return None
    return not stack


def bounded_stack(trace, max_depth=3):
    # Independent literal stack implementation used as the comparator reference.
    parents = []
    for op, ident in trace:
        if op == "open":
            if len(parents) >= max_depth:
                return None
            parents.append(ident)
        elif op == "close":
            if not parents or parents.pop() != ident:
                return False
        else:
            return None
    return len(parents) == 0


def all_traces(alphabet=("A", "B"), max_len=6):
    events = tuple(product(("open", "close"), alphabet))
    yield ()
    for n in range(1, max_len + 1):
        yield from product(events, repeat=n)


def run():
    traces = list(all_traces())
    valid_n = 0
    flat_wrong_accept = 0
    fsm_disagree = 0
    depth3 = 0
    unknown = 0
    for trace in traces:
        expected = valid(trace)
        flat = flat_flag(trace)
        fsm = bounded_fsm(trace)
        stack = bounded_stack(trace)
        if expected:
            valid_n += 1
        flat_balanced = flat and sum(1 if op == "open" else -1 for op, _ in trace) == 0
        if flat_balanced and not expected:
            flat_wrong_accept += 1
        if fsm is None:
            unknown += 1
        if fsm != stack:
            fsm_disagree += 1
        if expected and max((sum(1 if op == "open" else -1 for op, _ in trace[:i])
                             for i in range(len(trace) + 1)), default=0) <= 3:
            depth3 += 1
    return {
        "traces": len(traces),
        "valid_balanced_parent_traces": valid_n,
        "flat_flag_wrong_parent_acceptances": flat_wrong_accept,
        "depth3_valid_traces": depth3,
        "depth_matched_fsm_stack_disagreements": fsm_disagree,
        "bounded_unknowns": unknown,
        "claim": "finite-alphabet, length<=6 exact enumeration only",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), sort_keys=True, indent=2))

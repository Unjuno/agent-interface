"""Independent exhaustive stationary-policy oracle; no horizon recurrence."""
from typing import Any


def evaluate(case: dict[str, Any], start: str | None = None) -> dict[str, Any]:
    origin = case['start'] if start is None else start
    goals = set(case['goal_states'])
    controllable = [e for e in case['edges'] if e['kind'] == 'C']
    mandatory = [e for e in case['edges'] if e['kind'] == 'U']
    best = None
    nonblocking = False
    witness = None
    for mask in range(1 << len(controllable)):
        chosen = [e for j, e in enumerate(controllable) if mask & (1 << j)]
        enabled = mandatory + chosen
        outgoing: dict[str, list] = {}
        for e in enabled:
            outgoing.setdefault(e['source'], []).append(e)
        reached, pending = set(), [origin]
        while pending:
            s = pending.pop()
            if s in reached:
                continue
            reached.add(s)
            if s not in goals:
                pending.extend(e['target'] for e in outgoing.get(s, []))
        if any(not e['safe'] or not e['evidence_available'] for s in reached - goals
               for e in outgoing.get(s, [])):
            continue
        # For ordinary nonblocking, a path to a goal is required from every
        # reachable state. Cycles may still be legal; no fairness is assumed.
        def can_finish(s: str) -> bool:
            visited, queue = set(), [s]
            while queue:
                t = queue.pop()
                if t in goals:
                    return True
                if t not in visited:
                    visited.add(t)
                    queue.extend(e['target'] for e in outgoing.get(t, []))
            return False
        if not all(can_finish(s) for s in reached):
            continue
        nonblocking = True
        # Reject a reachable non-goal cycle; otherwise enumerate path lengths.
        def longest(s: str, active: frozenset[str]) -> int | None:
            if s in goals:
                return 0
            if s in active or not outgoing.get(s):
                return None
            lengths = [longest(e['target'], active | {s}) for e in outgoing[s]]
            if any(v is None for v in lengths):
                return None
            return 1 + max(lengths)
        length = longest(origin, frozenset())
        if length is not None and (best is None or length < best):
            best, witness = length, sorted(e['id'] for e in chosen)
    return {'bound': best, 'nonblocking': nonblocking, 'witness': witness,
            'masks': 1 << len(controllable)}

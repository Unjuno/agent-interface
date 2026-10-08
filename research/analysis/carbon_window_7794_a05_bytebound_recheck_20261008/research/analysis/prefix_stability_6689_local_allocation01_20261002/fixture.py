"""Frozen finite prefix-stability contract; no external inputs."""

START = (0, False, False, False, False, False, False, False, False, False, False)
FIELDS = ("generation", "sealed", "invalidated", "mandatory_fail", "mandatory_all_pass",
          "source_a_negative", "source_b_negative", "source_a_closed", "source_b_closed",
          "source_a_timeout", "source_b_timeout")


def successors(s):
    """All legal single-event transitions from a state."""
    g, sealed, invalidated, mf, mp, an, bn, ac, bc, at, bt = s
    out = []
    if not mf and not mp:
        out.extend([("mandatory_fail", s[:3] + (True,) + s[4:]),
                    ("mandatory_all_pass", s[:4] + (True,) + s[5:])])
    if not ac:
        if not an:
            out.append(("source_a_negative", s[:5] + (True,) + s[6:]))
        out.append(("source_a_closed", s[:7] + (True,) + s[8:]))
        if not at:
            out.append(("source_a_timeout", s[:9] + (True,) + s[10:]))
    if not bc:
        if not bn:
            out.append(("source_b_negative", s[:6] + (True,) + s[7:]))
        out.append(("source_b_closed", s[:8] + (True,) + s[9:]))
        if not bt:
            out.append(("source_b_timeout", s[:10] + (True,)))
    if not sealed:
        out.append(("generation_sealed", s[:1] + (True,) + s[2:]))
    if g == 0 and not sealed and not invalidated:
        out.append(("generation_invalidated", (1, False, True, False, False, False, False,
                                                False, False, False, False)))
    return out


def terminal(s):
    _, _, _, mf, mp, an, bn, ac, bc, _, _ = s
    if mf or an or bn:
        return "FAIL"
    if mp and ac and bc:
        return "PASS"
    return "UNKNOWN"


def classify(s, outcomes):
    if len(outcomes) == 1:
        return "STABLE_FINAL_" + next(iter(outcomes))
    _, _, _, mf, mp, an, bn, ac, bc, _, _ = s
    if mp and not mf and not an and not bn and not (ac and bc):
        return "CLOSED_FRONTIER_REQUIRED"
    return "PROVISIONAL"


def reachable():
    """Enumerate every distinct state reachable from START, retaining one prefix."""
    paths = {START: ()}
    queue = [START]
    for s in queue:
        for event, nxt in successors(s):
            if nxt not in paths:
                paths[nxt] = paths[s] + (event,)
                queue.append(nxt)
    return paths

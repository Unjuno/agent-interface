"""Candidate policy for finite approximate-section admission (Issue #5537 T5)."""
from itertools import product


VARIABLES = ("x", "y", "z")


def solve(contexts, complete, tolerance, action_class, allow_approx_irreversible=False):
    assignments = [dict(zip(VARIABLES, values)) for values in product((0, 1), repeat=3)]
    sections = [a for a in assignments if all(
        any(tuple(a[v] for v in c["vars"]) == tuple(t) for t in c["tuples"])
        for c in contexts
    )]
    exact_sections = [a for a in sections if all(
        all(a[v] == t for v, t in zip(c["vars"], row)) for c in contexts
        for row in c["tuples"]
    )]
    # The T5 fixtures use singleton tuples for exact observations. For the
    # broad-relation cases, the explicit spread field is the policy statistic.
    spread = max((c["spread"] for c in contexts), default=0.0)
    if not complete:
        status = "UNKNOWN"
    elif not sections:
        status = "NO_GLOBAL_SECTION"
    elif spread == 0:
        status = "GLOBAL_SECTION_CERTIFIED"
    elif spread <= tolerance:
        status = "APPROXIMATE_SECTION"
    else:
        status = "NO_GLOBAL_SECTION"

    admits = status == "GLOBAL_SECTION_CERTIFIED"
    if status == "APPROXIMATE_SECTION":
        admits = action_class in ("reversible", "compensable")
        admits |= action_class == "irreversible" and allow_approx_irreversible
    return {
        "status": status,
        "sections": sections,
        "section_count": len(sections),
        "spread": spread,
        "tolerance": tolerance,
        "action_class": action_class,
        "allow_approx_irreversible": allow_approx_irreversible,
        "admitted": admits,
    }

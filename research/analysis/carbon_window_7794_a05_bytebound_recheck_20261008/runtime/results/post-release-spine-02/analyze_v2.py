"""Versioned deterministic wrapper for the retained post-release-spine-02 audit."""
from analyze import analyze as _analyze


def analyze(root):
    result = _analyze(root)
    # Refusals are an inventory keyed by attempt, not a chronological trace.
    # Canonicalize this one field only; preserve ordering everywhere else.
    for route in result["routes"].values():
        route["refusals"].sort(key=lambda item: item["attempt"])
    return result

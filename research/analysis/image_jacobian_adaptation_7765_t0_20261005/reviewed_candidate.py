"""Post-formal safe entry point that rejects a stale first observation."""
from __future__ import annotations

import candidate as frozen_candidate


def run_trial(arm, observe, act, **kwargs):
    """Validate initial freshness before delegating to the frozen controller."""
    initial = observe()
    if not isinstance(initial, dict) or not initial.get("fresh", False):
        return {"status": "yield_unbound_or_stale", "corrections": 0, "rows": []}

    first = [initial]

    def observe_with_validated_first_sample():
        return first.pop(0) if first else observe()

    return frozen_candidate.run_trial(
        arm, observe_with_validated_first_sample, act, **kwargs)

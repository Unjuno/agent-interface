"""Candidate typed-health interrupt for unauthored, input-free MAP01 coast.

This is a construction candidate, not an accepted operating threshold. The
six-point drop is replay-derived from one retained v39 trace and needs a
prospective live evaluation before adoption.
"""

from observable_signal_guard_v2 import ObservableSignalGuard, ObservableSignalPolicyMonitor


CANDIDATE_MAX_HEALTH_LOSS = 6


class _TypedHealthExtractor:
    def read(self, event):
        if (type(event) is not dict or event.get("event") != "typed_observation" or
                event.get("schema") != "doom-typed-observation-v1" or
                event.get("artifact_published") is not False or
                event.get("grants_input_authority") is not False):
            raise ValueError("non-authoritative typed observation required")
        row = event.get("signals", {}).get("health")
        if (type(row) is not dict or row.get("signal_id") != "health" or
                row.get("sequence") != event.get("sequence") or
                row.get("capture_ns") != event.get("capture_ns") or
                row.get("binding") != event.get("pointer_binding") or
                row.get("status") not in ("observed", "unknown") or
                (row.get("status") == "unknown" and row.get("value") is not None)):
            raise ValueError("health must bind the exact typed frame epoch")
        return row


class UnauthoredCoastMonitor(ObservableSignalPolicyMonitor):
    """Invalidate a no-authority coast after candidate health loss or unknown."""

    event_types = frozenset({"typed_observation"})

    def __init__(self, source_signal, index):
        if (type(source_signal) is not dict or source_signal.get("status") != "observed" or
                source_signal.get("signal_id") != "health" or
                type(source_signal.get("value")) is not int or
                type(source_signal.get("sequence")) is not int or
                type(source_signal.get("capture_ns")) is not int or
                type(source_signal.get("binding")) is not dict):
            raise ValueError("observed bound source health required")
        source_value = source_signal["value"]
        if not 1 <= source_value <= 1_000_000:
            raise ValueError("bounded positive source health required")
        spec = {
            "op": "observable_signal_guard",
            "guard_id": f"map01-coast-candidate-{index}",
            "source_sequence": source_signal["sequence"],
            "signal_id": "health",
            "source_value": source_value,
            # Guard invalidates below hard_minimum, so loss >= 6 trips it.
            "hard_minimum": max(0, source_value - CANDIDATE_MAX_HEALTH_LOSS + 1),
            "max_source_age_ms": 30000,
            "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision",
            "on_unknown": "needs_decision",
        }
        guard = ObservableSignalGuard(spec, source_signal, source_signal["binding"])
        super().__init__(guard, _TypedHealthExtractor())


def wait_for_fresh_observation(wait, invalidation_sequence, latest_observation=None):
    """Do not replan from a stale screenshot after early typed invalidation."""
    if type(invalidation_sequence) is not int or invalidation_sequence < 0:
        raise ValueError("nonnegative integer invalidation sequence required")
    current = latest_observation() if callable(latest_observation) else latest_observation
    if (type(current) is dict and current.get("event") == "observation" and
            type(current.get("sequence")) is int and
            current["sequence"] >= invalidation_sequence):
        return current
    return wait(lambda row: (
        type(row) is dict and row.get("event") == "observation" and
        type(row.get("sequence")) is int and
        row["sequence"] >= invalidation_sequence))


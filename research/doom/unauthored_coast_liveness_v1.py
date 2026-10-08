"""Candidate typed-health interrupt for unauthored, input-free MAP01 coast.

This is a construction candidate, not an accepted operating threshold. The
five-point, two-of-three rule is replay-derived from retained v38/v39 traces
and needs prospective evaluation before adoption.
"""

from collections import deque

from observable_signal_guard_v2 import ObservableSignalGuard, ObservableSignalPolicyMonitor


CANDIDATE_MIN_HEALTH_DROP = 5
CANDIDATE_LOW_SAMPLES = 2
CANDIDATE_WINDOW_SAMPLES = 3


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
    """Apply a bounded 2-of-3 drop rule; unknown/expired evidence fails closed."""

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
        self.candidate_baseline = source_value
        self.candidate_low_samples = deque(maxlen=CANDIDATE_WINDOW_SAMPLES)
        spec = {
            "op": "observable_signal_guard",
            "guard_id": f"map01-coast-candidate-{index}",
            "source_sequence": source_signal["sequence"],
            "signal_id": "health",
            "source_value": source_value,
            # Death/unavailable/expired signals still invalidate immediately;
            # the exploratory damage trigger is handled by the 2-of-3 window.
            "hard_minimum": 1,
            "max_source_age_ms": 30000,
            "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision",
            "on_unknown": "needs_decision",
        }
        guard = ObservableSignalGuard(spec, source_signal, source_signal["binding"])
        super().__init__(guard, _TypedHealthExtractor())

    def observe(self, observation):
        event = super().observe(observation)
        if event is not None:
            return event
        # `super` already validated monotonic sequence, signal binding, age and
        # extraction. Re-read only the compact health record for the bounded
        # rolling candidate rule.
        signal = self.extractor.read(observation)
        value = signal.get("value")
        low = (signal.get("status") == "observed" and type(value) is int and
               value <= self.candidate_baseline - CANDIDATE_MIN_HEALTH_DROP)
        self.candidate_low_samples.append({
            "sequence": observation["sequence"], "value": value, "low": low})
        low_rows = [row for row in self.candidate_low_samples if row["low"]]
        if len(low_rows) < CANDIDATE_LOW_SAMPLES:
            return None
        return {
            "sequence": observation["sequence"],
            "signal": signal,
            "outcome": {
                "status": "HARD_INVALIDATED",
                "reason": "two_of_three_below_candidate_baseline",
                "source_value": self.candidate_baseline,
                "current_value": value,
                "candidate_threshold": self.candidate_baseline - CANDIDATE_MIN_HEALTH_DROP,
                "window_sequences": [row["sequence"] for row in self.candidate_low_samples],
                "low_samples_in_window": len(low_rows),
                "requires_new_decision": True,
                "grants_input_authority": False,
                "may_only_preserve_or_reduce_existing_authority": True,
                "semantic_change_identified": True,
                "task_success_verified": False,
            },
        }


def invalidation_handoff_sequence(invalidation_sequence, latest_observation):
    """Choose the paired frame sequence, or the next fresh one if malformed."""
    if type(invalidation_sequence) is int and invalidation_sequence >= 0:
        return invalidation_sequence
    if (type(latest_observation) is not dict or
            latest_observation.get("event") != "observation" or
            type(latest_observation.get("sequence")) is not int or
            latest_observation["sequence"] < 0):
        raise ValueError("latest observation required to recover invalid sequence")
    return latest_observation["sequence"] + 1


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

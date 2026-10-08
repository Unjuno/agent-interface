"""One-way typed signal validity envelope for already admitted authority."""
import json


FIELDS = {
    "op", "guard_id", "source_sequence", "signal_id", "source_value",
    "hard_minimum", "max_source_age_ms", "on_soft_change", "on_hard_change",
    "on_unknown",
}


def binding_key(binding):
    return json.dumps(binding, sort_keys=True, separators=(",", ":"))


def validate(spec, current_sequence):
    if type(spec) is not dict or set(spec) != FIELDS:
        raise ValueError("exact observable signal guard fields required")
    if spec["op"] != "observable_signal_guard":
        raise ValueError("observable_signal_guard op required")
    if not isinstance(spec["guard_id"], str) or not 1 <= len(spec["guard_id"]) <= 64:
        raise ValueError("bounded guard_id required")
    if type(spec["source_sequence"]) is not int or spec["source_sequence"] != current_sequence:
        raise ValueError("latest source_sequence required")
    if not isinstance(spec["signal_id"], str) or not 1 <= len(spec["signal_id"]) <= 64:
        raise ValueError("bounded signal_id required")
    if type(spec["source_value"]) is not int or type(spec["hard_minimum"]) is not int:
        raise ValueError("integer source_value and hard_minimum required")
    if not 0 <= spec["hard_minimum"] <= spec["source_value"] <= 1_000_000:
        raise ValueError("hard_minimum must not exceed bounded source_value")
    if (type(spec["max_source_age_ms"]) is not int or
            not 100 <= spec["max_source_age_ms"] <= 30000):
        raise ValueError("max_source_age_ms must be integer 100..30000")
    if (spec["on_soft_change"] != "preserve_existing_policy" or
            spec["on_hard_change"] != "needs_decision" or
            spec["on_unknown"] != "needs_decision"):
        raise ValueError("one-way authority outcomes required")
    return dict(spec)


class ObservableSignalGuard:
    def __init__(self, spec, source_signal, binding):
        if type(source_signal) is not dict or source_signal.get("status") != "observed":
            raise ValueError("observed source signal required")
        self.spec = validate(spec, source_signal.get("sequence"))
        if (source_signal.get("signal_id") != self.spec["signal_id"] or
                source_signal.get("value") != self.spec["source_value"]):
            raise ValueError("source signal/spec mismatch")
        if type(source_signal.get("capture_ns")) is not int or source_signal["capture_ns"] <= 0:
            raise ValueError("positive source capture required")
        if type(binding) is not dict or not binding:
            raise ValueError("nonempty source binding required")
        if binding_key(source_signal.get("binding")) != binding_key(binding):
            raise ValueError("source signal/binding mismatch")
        self.source_capture_ns = source_signal["capture_ns"]
        self.source_binding = binding_key(binding)

    def evaluate(self, current_signal):
        if type(current_signal) is not dict or current_signal.get("status") != "observed":
            return self._outcome("UNKNOWN", "signal_unavailable", None, None)
        if current_signal.get("signal_id") != self.spec["signal_id"]:
            return self._outcome("UNKNOWN", "signal_changed", None, None)
        if binding_key(current_signal.get("binding")) != self.source_binding:
            return self._outcome("UNKNOWN", "binding_changed", None, None)
        sequence = current_signal.get("sequence")
        sampled_ns = current_signal.get("capture_ns")
        if type(sequence) is not int or sequence <= self.spec["source_sequence"]:
            return self._outcome("UNKNOWN", "nonadvancing_sequence", None, None)
        if type(sampled_ns) is not int or sampled_ns <= self.source_capture_ns:
            return self._outcome("UNKNOWN", "invalid_sample_time", None, None)
        age_ms = (sampled_ns - self.source_capture_ns) / 1e6
        if age_ms > self.spec["max_source_age_ms"]:
            return self._outcome("UNKNOWN", "source_expired", current_signal.get("value"), age_ms)
        value = current_signal.get("value")
        if type(value) is not int or not 0 <= value <= 1_000_000:
            return self._outcome("UNKNOWN", "invalid_signal_value", None, age_ms)
        if value < self.spec["hard_minimum"]:
            return self._outcome("HARD_INVALIDATED", "below_hard_minimum", value, age_ms)
        if value != self.spec["source_value"]:
            return self._outcome("SOFT_CHANGED", "within_validity_envelope", value, age_ms)
        return self._outcome("UNCHANGED", "signal_unchanged", value, age_ms)

    def _outcome(self, status, reason, current_value, source_age_ms):
        keep = status in ("UNCHANGED", "SOFT_CHANGED")
        return {
            "format": "observable-signal-guard-outcome-v1",
            "guard_id": self.spec["guard_id"], "signal_id": self.spec["signal_id"],
            "status": status, "reason": reason,
            "source_value": self.spec["source_value"], "current_value": current_value,
            "hard_minimum": self.spec["hard_minimum"], "source_age_ms": source_age_ms,
            "keep_existing_policy": keep, "requires_new_decision": not keep,
            "grants_input_authority": False,
            "may_only_preserve_or_reduce_existing_authority": True,
            "semantic_change_identified": status == "SOFT_CHANGED" or status == "HARD_INVALIDATED",
            "task_success_verified": False,
        }


class ObservableSignalPolicyMonitor:
    """Coalesce soft events and surface only hard/unknown invalidation."""

    def __init__(self, guard, extractor):
        self.guard = guard
        self.extractor = extractor
        self.last_sequence = guard.spec["source_sequence"]
        self.last_signal_value = guard.spec["source_value"]
        self.soft_event_count = 0
        self.latest_soft_event = None

    def observe(self, observation):
        sequence = observation.get("sequence")
        if type(sequence) is not int or sequence <= self.last_sequence:
            signal = {"status": "unknown"}
        else:
            self.last_sequence = sequence
            try:
                signal = self.extractor.read(observation)
            except (OSError, ValueError, TypeError):
                signal = {"status": "unknown"}
        outcome = self.guard.evaluate(signal)
        event = {"sequence": sequence, "signal": signal, "outcome": outcome}
        if outcome["status"] == "SOFT_CHANGED":
            if outcome["current_value"] != self.last_signal_value:
                self.soft_event_count += 1
                self.latest_soft_event = event
                self.last_signal_value = outcome["current_value"]
            return None
        if outcome["status"] == "UNCHANGED":
            self.last_signal_value = outcome["current_value"]
        return None if outcome["status"] == "UNCHANGED" else event

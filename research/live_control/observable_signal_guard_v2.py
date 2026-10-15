"""One-way typed signal validity envelope with monitor-stage clocks."""
import json
import time


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

    event_types = frozenset(("observation", "typed_observation"))

    def __init__(self, guard, extractor):
        self.guard = guard
        self.extractor = extractor
        self.last_sequence = guard.spec["source_sequence"]
        self.last_capture_ns = guard.source_capture_ns
        self.seen_event_kinds = set()
        self.last_event_kind = None
        self.last_signal = None
        self.last_frame_rgb_sha256 = None
        self.last_signal_value = guard.spec["source_value"]
        self.soft_event_count = 0
        self.latest_soft_event = None

    def _typed_signal(self, observation):
        # Lazy dependency: generic artifact-only monitors need no DOOM module.
        # Support both package tests and the existing direct DOOM script entry.
        try:
            from research.doom.doom_signal_value_domain_v1 import signal_value_in_domain
        except ModuleNotFoundError:
            from doom_signal_value_domain_v1 import signal_value_in_domain
        if (type(observation) is not dict or
                observation.get("event") != "typed_observation" or
                observation.get("schema") != "doom-typed-observation-v1" or
                observation.get("artifact_published") is not False or
                observation.get("grants_input_authority") is not False):
            return {"status": "unknown"}
        sequence = observation.get("sequence")
        capture_ns = observation.get("capture_ns")
        binding = observation.get("pointer_binding")
        frame_size = observation.get("frame_size")
        digest = observation.get("frame_rgb_sha256")
        started_ns = observation.get("typed_extraction_started_ns")
        ready_ns = observation.get("typed_ready_ns")
        signals = observation.get("signals")
        if (type(sequence) is not int or sequence < 1 or
                type(capture_ns) is not int or capture_ns < 1 or
                type(binding) is not dict or not binding or
                type(frame_size) is not list or len(frame_size) != 2 or
                any(type(value) is not int or value <= 0 for value in frame_size) or
                type(digest) is not str or len(digest) != 64 or
                any(c not in "0123456789abcdef" for c in digest) or
                type(started_ns) is not int or type(ready_ns) is not int or
                not capture_ns <= started_ns <= ready_ns or
                type(signals) is not dict or set(signals) != {"health", "ammo"}):
            return {"status": "unknown"}
        for name, row in signals.items():
            if (type(row) is not dict or
                    row.get("format") != "observable-signal-v1" or
                    row.get("signal_id") != name or
                    row.get("status") not in ("observed", "unknown") or
                    (row.get("status") == "unknown" and row.get("value") is not None) or
                    (row.get("status") == "observed" and
                     not signal_value_in_domain(name, row.get("value"))) or
                    type(row.get("sequence")) is not int or
                    type(row.get("capture_ns")) is not int or
                    row.get("sequence") != sequence or
                    row.get("capture_ns") != capture_ns or
                    type(row.get("binding")) is not dict or
                    binding_key(row.get("binding")) != binding_key(binding) or
                    type(row.get("wad_sha256")) is not str or
                    len(row["wad_sha256"]) != 64 or
                    any(c not in "0123456789abcdef" for c in row["wad_sha256"])):
                return {"status": "unknown"}
        return signals.get(self.guard.spec["signal_id"], {"status": "unknown"})

    @staticmethod
    def _same_signal(left, right):
        fields = ("format", "status", "signal_id", "value", "sequence",
                  "capture_ns", "wad_sha256")
        if type(left) is not dict or type(right) is not dict:
            return False
        if not all(type(left.get(field)) is type(right.get(field)) and
                   left.get(field) == right.get(field) for field in fields):
            return False
        if type(left.get("binding")) is not dict or type(right.get("binding")) is not dict:
            return False
        return binding_key(left["binding"]) == binding_key(right["binding"])

    def observe(self, observation):
        monitor_received_ns = time.perf_counter_ns()
        event_kind = observation.get("event", "observation") if type(observation) is dict else None
        sequence = observation.get("sequence") if type(observation) is dict else None
        paired_duplicate = (
            type(sequence) is int and sequence == self.last_sequence and
            event_kind in self.event_types and self.last_event_kind in self.event_types and
            event_kind not in self.seen_event_kinds and len(self.seen_event_kinds) == 1
        )
        if paired_duplicate:
            try:
                signal = (self._typed_signal(observation)
                          if event_kind == "typed_observation"
                          else self.extractor.read(observation))
            except (OSError, ValueError, TypeError, KeyError):
                signal = {"status": "unknown"}
            frame_hash_matches = (
                type(observation.get("frame_rgb_sha256")) is str and
                observation.get("frame_rgb_sha256") == self.last_frame_rgb_sha256)
            if self._same_signal(signal, self.last_signal) and frame_hash_matches:
                self.seen_event_kinds.add(event_kind)
                self.last_event_kind = event_kind
                self.last_signal = signal
                return None
            signal = {"status": "unknown"}
        elif (type(sequence) is not int or sequence <= self.last_sequence or
              event_kind not in self.event_types):
            signal = {"status": "unknown"}
        else:
            self.last_sequence = sequence
            try:
                signal = (self._typed_signal(observation)
                          if event_kind == "typed_observation"
                          else self.extractor.read(observation))
            except (OSError, ValueError, TypeError, KeyError):
                signal = {"status": "unknown"}
            capture_ns = signal.get("capture_ns") if type(signal) is dict else None
            if type(capture_ns) is not int or capture_ns <= self.last_capture_ns:
                signal = {"status": "unknown"}
            else:
                self.last_capture_ns = capture_ns
            self.seen_event_kinds = {event_kind}
            self.last_event_kind = event_kind
            self.last_signal = signal
            self.last_frame_rgb_sha256 = observation.get("frame_rgb_sha256")
        signal_extracted_ns = time.perf_counter_ns()
        outcome = self.guard.evaluate(signal)
        outcome_evaluated_ns = time.perf_counter_ns()
        event = {"sequence": sequence, "signal": signal, "outcome": outcome,
                 "source_event_kind": event_kind,
                 "monitor_received_ns": monitor_received_ns,
                 "signal_extracted_ns": signal_extracted_ns,
                 "outcome_evaluated_ns": outcome_evaluated_ns,
                 "signal_extraction_ms": (signal_extracted_ns - monitor_received_ns) / 1e6,
                 "outcome_evaluation_ms": (outcome_evaluated_ns - signal_extracted_ns) / 1e6}
        if outcome["status"] == "SOFT_CHANGED":
            if outcome["current_value"] != self.last_signal_value:
                self.soft_event_count += 1
                self.latest_soft_event = event
                self.last_signal_value = outcome["current_value"]
            return None
        if outcome["status"] == "UNCHANGED":
            self.last_signal_value = outcome["current_value"]
        return None if outcome["status"] == "UNCHANGED" else event

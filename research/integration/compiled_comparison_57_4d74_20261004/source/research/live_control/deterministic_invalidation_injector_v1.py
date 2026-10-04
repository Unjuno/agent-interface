"""One-shot, one-way invalidation injection for integration testing."""
import time


class CompositeInvalidationMonitor:
    """Preserve natural invalidation priority, then evaluate a test injector."""

    def __init__(self, natural, injected):
        self.natural = natural
        self.injected = injected

    def observe(self, observation):
        result = self.natural.observe(observation)
        return result if result is not None else self.injected.observe(observation)


class OneShotInvalidationInjector:
    """Fire once after N exact observations in one explicitly selected turn."""

    def __init__(self, *, target_iteration, after_observations, clock=None):
        if type(target_iteration) is not int or target_iteration < 0:
            raise ValueError("target_iteration must be a non-negative integer")
        if type(after_observations) is not int or after_observations < 1:
            raise ValueError("after_observations must be a positive integer")
        self.target_iteration = target_iteration
        self.after_observations = after_observations
        self.clock = clock or time.perf_counter_ns
        self.fired = False
        self.fire_record = None

    def bind(self, *, iteration, source_sequence):
        return _BoundInjection(self, iteration, source_sequence)


class _BoundInjection:
    def __init__(self, owner, iteration, source_sequence):
        self.owner = owner
        self.iteration = iteration
        self.source_sequence = source_sequence
        self.observations = 0
        self.last_sequence = source_sequence

    def observe(self, observation):
        if self.owner.fired or self.iteration != self.owner.target_iteration:
            return None
        sequence = observation.get("sequence")
        if type(sequence) is not int or sequence <= self.last_sequence:
            # The natural monitor must fail closed before an injector sees this.
            raise ValueError("injector received a nonadvancing exact sequence")
        self.last_sequence = sequence
        self.observations += 1
        if self.observations < self.owner.after_observations:
            return None
        detected_ns = self.owner.clock()
        record = {
            "outcome": {
                "format": "deterministic-invalidation-injection-v1",
                "status": "INJECTED_INVALIDATION",
                "reason": "preregistered_one_shot_integration_test",
                "keep_existing_policy": False,
                "requires_new_decision": True,
                "grants_input_authority": False,
                "may_only_reduce_existing_authority": True,
                "semantic_change_identified": False,
                "task_success_verified": False,
            },
            "sequence": sequence,
            "image": observation.get("image"),
            "capture_ns": observation.get("capture_ns"),
            "dequeued_ns": detected_ns,
            "evaluated_ns": detected_ns,
            "detected_ns": detected_ns,
            "evaluation_ms": 0.0,
            "injection": {
                "target_iteration": self.owner.target_iteration,
                "source_sequence": self.source_sequence,
                "after_observations": self.owner.after_observations,
                "observations_seen": self.observations,
            },
        }
        self.owner.fired = True
        self.owner.fire_record = record
        return record

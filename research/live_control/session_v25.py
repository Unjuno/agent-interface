"""Candidate X11 backend for fixed-region target-and-guard continuation checks."""
import time

import numpy as np

from executor_v3 import Cancelled, DecisionRequired
from local_target_guard_postcondition_v1 import LocalTargetGuardPostcondition
from local_visual_barrier_program_v1 import MUTATING
from session_v24 import Backend as Previous, suite


TARGET_GUARD_SCHEMA = {
    "op": "local_target_guard_postcondition",
    "placement": "immediately after bounded passive settle following an admitted mutation, and before a later admitted mutation",
    "comparison": "immutable source pixels versus 2..3 current samples in disjoint fixed target and guard boxes",
    "authority": "condition for already admitted later steps only; no semantic, task-success or new-input authority",
}


class Backend(Previous):
    def __init__(self, session, out, emit):
        super().__init__(session, out, emit)
        self.target_guard_postconditions = {}

    def pixels(self):
        return np.asarray(self.image()).copy()

    def validate(self, steps):
        rewritten = []
        conditions = {}
        total_timeout_ms = 0
        for index, step in enumerate(steps):
            if not isinstance(step, dict) or step.get("op") != "local_target_guard_postcondition":
                rewritten.append(step)
                continue
            if index == 0 or index + 1 >= len(steps):
                raise ValueError("postcondition must be between admitted steps")
            if not isinstance(steps[index - 1], dict) or steps[index - 1].get("op") != "settle":
                raise ValueError("target-guard postcondition must immediately follow bounded settle")
            if not any(isinstance(earlier, dict) and earlier.get("op") in MUTATING
                       for earlier in steps[:index - 1]):
                raise ValueError("postcondition must follow a mutating step")
            if not any(isinstance(later, dict) and later.get("op") in MUTATING
                       for later in steps[index + 1:]):
                raise ValueError("postcondition must guard a later mutating step")
            identifier = step.get("postcondition_id")
            if identifier in conditions:
                raise ValueError("postcondition_id must be unique within a program")
            conditions[identifier] = LocalTargetGuardPostcondition(
                step, self.pixels(), self.sequence, self.frame_identity())
            total_timeout_ms += step["timeout_ms"]
            rewritten.append({"op": "observe"})
        if total_timeout_ms > 3000:
            raise ValueError("combined target-guard postcondition timeout exceeds 3000ms")
        super().validate(rewritten)
        self.target_guard_postconditions = conditions

    def execute(self, step, cancel, identifier, index):
        if step["op"] != "local_target_guard_postcondition":
            return super().execute(step, cancel, identifier, index)
        condition = self.target_guard_postconditions.pop(step["postcondition_id"], None)
        if condition is None:
            raise DecisionRequired("local target-guard postcondition unavailable")
        samples = []
        sequences = []
        bindings = []
        sampled_ns = []
        for sample_index in range(condition.spec["required_samples"]):
            if sample_index:
                if cancel.wait(condition.spec["sample_interval_ms"] / 1000):
                    raise Cancelled()
                self.snapshot(identifier, index)
            if cancel.is_set():
                raise Cancelled()
            samples.append(self.pixels())
            sequences.append(self.sequence)
            bindings.append(self.frame_identity())
            sampled_ns.append(time.perf_counter_ns())
        outcome = condition.evaluate(samples, sequences, bindings, sampled_ns)
        self.emit({"event": "local_target_guard_postcondition", "id": identifier,
                   "step": index, "sequence": self.sequence, **outcome})
        if not outcome["continue_program"]:
            raise DecisionRequired("local target-guard postcondition " + outcome["reason"])
        return outcome

"""Prepare and run visual barriers inside an already admitted bounded program."""
from executor_v3 import Cancelled, DecisionRequired
from local_visual_barrier_v1 import LocalVisualBarrier


MUTATING = {
    "text", "key", "chord", "hold", "pointer_move", "pointer_click",
    "pointer_drag", "pointer_scroll", "pointer_guided", "pointer_servo",
}


def prepare(steps, source, source_sequence, binding):
    if type(steps) is not list or not steps:
        raise ValueError("nonempty program steps required")
    barriers = {}
    rewritten = []
    total_timeout_ms = 0
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or step.get("op") != "local_visual_barrier":
            rewritten.append(step)
            continue
        if index == 0 or index + 1 >= len(steps):
            raise ValueError("barrier must be between admitted steps")
        if not isinstance(steps[index - 1], dict) or steps[index - 1].get("op") not in MUTATING:
            raise ValueError("barrier must immediately follow a mutating step")
        if not any(isinstance(later, dict) and later.get("op") in MUTATING
                   for later in steps[index + 1:]):
            raise ValueError("barrier must guard a later mutating step")
        identifier = step.get("barrier_id")
        if identifier in barriers:
            raise ValueError("barrier_id must be unique within a program")
        barriers[identifier] = LocalVisualBarrier(step, source, source_sequence, binding)
        total_timeout_ms += step["timeout_ms"]
        rewritten.append({"op": "observe"})
    if total_timeout_ms > 3000:
        raise ValueError("combined local visual barrier timeout exceeds 3000ms")
    return rewritten, barriers


def run(step, barrier, capture, cancel, emit):
    if step.get("barrier_id") != barrier.spec["barrier_id"]:
        raise DecisionRequired("local visual barrier identity unavailable")
    samples = []
    bindings = []
    sampled_ns = []
    for index in range(barrier.spec["required_samples"]):
        if index and cancel.wait(barrier.spec["sample_interval_ms"] / 1000):
            raise Cancelled()
        if cancel.is_set():
            raise Cancelled()
        image, binding, captured_ns = capture()
        samples.append(image)
        bindings.append(binding)
        sampled_ns.append(captured_ns)
    outcome = barrier.evaluate(samples, bindings, sampled_ns)
    emit(outcome)
    if not outcome["continue_program"]:
        raise DecisionRequired("local visual barrier " + outcome["reason"])
    return outcome

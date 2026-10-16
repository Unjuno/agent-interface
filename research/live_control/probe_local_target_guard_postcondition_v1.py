"""Pure positive, partial, guard and refusal probes for target/guard v1."""
import json

import numpy as np

from local_target_guard_postcondition_v1 import LocalTargetGuardPostcondition


def spec():
    return {
        "op": "local_target_guard_postcondition",
        "postcondition_id": "placement-a",
        "source_sequence": 7,
        "target_boxes": [[2, 2, 4, 4]],
        "guard_boxes": [[10, 2, 4, 4]],
        "pixel_delta_threshold": 24,
        "minimum_target_changed_pixels": 8,
        "maximum_guard_changed_pixels": 0,
        "required_samples": 2,
        "sample_interval_ms": 50,
        "timeout_ms": 500,
        "on_unmet": "needs_decision",
    }


def evaluate(condition, frames, bindings=None, times=None):
    return condition.evaluate(frames, [8, 9], bindings or ["surface-a", "surface-a"],
                              times or [1_000_000_000, 1_050_000_000])


def refusal(mutator):
    source = np.zeros((20, 20, 3), dtype=np.uint8)
    candidate = spec()
    mutator(candidate)
    try:
        LocalTargetGuardPostcondition(candidate, source, 7, "surface-a")
    except ValueError as error:
        return str(error)
    raise AssertionError("refusal expected")


def main():
    source = np.zeros((20, 20, 3), dtype=np.uint8)
    target = source.copy(); target[2:6, 2:6] = 64
    partial = source.copy(); partial[2:4, 2:5] = 64
    unsafe = target.copy(); unsafe[2, 10] = 64
    condition = LocalTargetGuardPostcondition(spec(), source, 7, "surface-a")
    outcomes = {
        "met": evaluate(condition, [target, target]),
        "partial": evaluate(condition, [partial, partial]),
        "guard": evaluate(condition, [unsafe, unsafe]),
        "transient": evaluate(condition, [target, partial]),
        "binding": evaluate(condition, [target, target], ["surface-a", "surface-b"]),
        "timeout": evaluate(condition, [target, target], times=[1_000_000_000, 1_600_000_000]),
    }
    assert outcomes["met"]["reason"] == "met" and outcomes["met"]["continue_program"]
    assert outcomes["partial"]["reason"] == "target_not_reached"
    assert outcomes["guard"]["reason"] == "guard_changed"
    assert outcomes["transient"]["reason"] == "target_not_reached"
    assert outcomes["binding"]["reason"] == "binding_changed"
    assert outcomes["timeout"]["reason"] == "timeout"
    refusals = {
        "overlap": refusal(lambda value: value.update(guard_boxes=[[4, 4, 4, 4]])),
        "stale": refusal(lambda value: value.update(source_sequence=6)),
        "target_threshold": refusal(lambda value: value.update(minimum_target_changed_pixels=17)),
        "guard_threshold": refusal(lambda value: value.update(maximum_guard_changed_pixels=16)),
        "one_sample": refusal(lambda value: value.update(required_samples=1)),
        "unbounded_wait": refusal(lambda value: value.update(timeout_ms=3001)),
        "unsafe_unmet": refusal(lambda value: value.update(on_unmet="continue")),
    }
    report = {
        "probe_passed": True,
        "outcomes": {name: outcome["reason"] for name, outcome in outcomes.items()},
        "refusals": refusals,
        "decision": "advance to archived OpenTTD calibration; no live-input promotion",
        "scope": "pure synthetic arrays only; no application, semantic, latency or generalization claim",
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

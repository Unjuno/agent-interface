"""Read-only task-relative patch displacement postcondition."""
from visual_anchor import VisualAnchor


FIELDS = {
    "op", "postcondition_id", "source_sequence", "box", "target_delta",
    "tolerance_px", "required_samples", "sample_interval_ms", "timeout_ms",
    "on_unmet",
}


def validate(spec, image_shape, current_sequence):
    if type(spec) is not dict or set(spec) != FIELDS:
        raise ValueError("exact local displacement postcondition fields required")
    if spec["op"] != "local_displacement_postcondition":
        raise ValueError("local_displacement_postcondition op required")
    if not isinstance(spec["postcondition_id"], str) or not 1 <= len(spec["postcondition_id"]) <= 64:
        raise ValueError("bounded postcondition_id required")
    if type(spec["source_sequence"]) is not int or spec["source_sequence"] != current_sequence:
        raise ValueError("latest source_sequence required")
    if type(spec["box"]) is not list or len(spec["box"]) != 4 or any(type(v) is not int for v in spec["box"]):
        raise ValueError("integer [x,y,width,height] box required")
    x, y, width, height = spec["box"]
    frame_height, frame_width, channels = image_shape
    if channels != 3 or min(width, height) < 4 or max(width, height) > 96:
        raise ValueError("RGB patch size 4..96 required")
    if x < 0 or y < 0 or x + width > frame_width or y + height > frame_height:
        raise ValueError("patch outside source frame")
    if type(spec["target_delta"]) is not list or len(spec["target_delta"]) != 2 or \
            any(type(value) is not int or abs(value) > 32 for value in spec["target_delta"]):
        raise ValueError("bounded integer target_delta required")
    if type(spec["tolerance_px"]) is not int or not 0 <= spec["tolerance_px"] <= 3:
        raise ValueError("tolerance_px must be integer 0..3")
    if type(spec["required_samples"]) is not int or not 2 <= spec["required_samples"] <= 3:
        raise ValueError("required_samples must be integer 2..3")
    if type(spec["sample_interval_ms"]) is not int or not 20 <= spec["sample_interval_ms"] <= 500:
        raise ValueError("sample_interval_ms must be integer 20..500")
    if type(spec["timeout_ms"]) is not int or not 100 <= spec["timeout_ms"] <= 3000:
        raise ValueError("timeout_ms must be integer 100..3000")
    if (spec["required_samples"] - 1) * spec["sample_interval_ms"] > spec["timeout_ms"]:
        raise ValueError("required samples do not fit timeout")
    if spec["on_unmet"] != "needs_decision":
        raise ValueError("unmet postcondition must require a decision")
    return dict(spec)


class LocalDisplacementPostcondition:
    def __init__(self, spec, source, source_sequence, binding):
        self.spec = validate(spec, source.shape, source_sequence)
        if not isinstance(binding, str) or not binding:
            raise ValueError("nonempty source binding required")
        self.binding = binding
        self.anchor = VisualAnchor(source, self.spec["box"], source_sequence, binding)

    def evaluate(self, samples, sequences, bindings, sampled_ns):
        required = self.spec["required_samples"]
        if not all(type(values) is list for values in (samples, sequences, bindings, sampled_ns)):
            raise ValueError("sample metadata lists required")
        if not len(samples) == len(sequences) == len(bindings) == len(sampled_ns) == required:
            raise ValueError("exact required sample count required")
        if any(type(value) is not int or value <= 0 for value in sampled_ns):
            raise ValueError("positive integer sample times required")
        if sampled_ns != sorted(sampled_ns) or len(set(sampled_ns)) != len(sampled_ns):
            raise ValueError("strictly increasing sample times required")
        span_ms = (sampled_ns[-1] - sampled_ns[0]) / 1e6
        if span_ms > self.spec["timeout_ms"]:
            return self._outcome("timeout", [], span_ms)
        if any(binding != self.binding for binding in bindings):
            return self._outcome("binding_changed", [], span_ms)
        results = [self.anchor.locate(image, sequence, binding)
                   for image, sequence, binding in zip(samples, sequences, bindings)]
        bad = next((result["status"] for result in results if result["status"] != "matched"), None)
        if bad is not None:
            return self._outcome(bad, results, span_ms)
        target = self.spec["target_delta"]
        tolerance = self.spec["tolerance_px"]
        reached = all(max(abs(actual - expected) for actual, expected in zip(result["delta"], target)) <= tolerance
                      for result in results)
        return self._outcome("met" if reached else "target_not_reached", results, span_ms)

    def _outcome(self, reason, tracking, sample_span_ms):
        return {
            "format": "local-displacement-postcondition-outcome-v1",
            "postcondition_id": self.spec["postcondition_id"],
            "reason": reason,
            "continue_program": reason == "met",
            "needs_decision": reason != "met",
            "target_delta": self.spec["target_delta"],
            "tolerance_px": self.spec["tolerance_px"],
            "tracking": tracking,
            "sample_span_ms": sample_span_ms,
            "semantic_effect_verified": False,
            "task_success_verified": False,
            "grants_input_authority": False,
            "scope": "task-relative visual condition for already admitted later steps only",
        }

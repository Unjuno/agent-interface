"""Read-only fixed-region target-and-guard visual postcondition."""
import numpy as np


FIELDS = {
    "op", "postcondition_id", "source_sequence", "target_boxes", "guard_boxes",
    "pixel_delta_threshold", "minimum_target_changed_pixels",
    "maximum_guard_changed_pixels", "required_samples", "sample_interval_ms",
    "timeout_ms", "on_unmet",
}


def _boxes(value, name, frame_width, frame_height):
    if type(value) is not list or not 1 <= len(value) <= 16:
        raise ValueError(f"{name} must contain 1..16 boxes")
    normalized = []
    for box in value:
        if type(box) is not list or len(box) != 4 or any(type(v) is not int for v in box):
            raise ValueError(f"{name} boxes must be integer [x,y,width,height]")
        x, y, width, height = box
        if min(width, height) < 2 or max(width, height) > 128:
            raise ValueError(f"{name} box dimensions must be 2..128")
        if x < 0 or y < 0 or x + width > frame_width or y + height > frame_height:
            raise ValueError(f"{name} box outside source frame")
        normalized.append(tuple(box))
    if sum(width * height for _, _, width, height in normalized) > 65536:
        raise ValueError(f"{name} total area exceeds 65536 pixels")
    return normalized


def _overlap(left, right):
    lx, ly, lw, lh = left
    rx, ry, rw, rh = right
    return lx < rx + rw and rx < lx + lw and ly < ry + rh and ry < ly + lh


def validate(spec, image_shape, current_sequence):
    if type(spec) is not dict or set(spec) != FIELDS:
        raise ValueError("exact local target-guard postcondition fields required")
    if spec["op"] != "local_target_guard_postcondition":
        raise ValueError("local_target_guard_postcondition op required")
    if not isinstance(spec["postcondition_id"], str) or not 1 <= len(spec["postcondition_id"]) <= 64:
        raise ValueError("bounded postcondition_id required")
    if type(spec["source_sequence"]) is not int or spec["source_sequence"] != current_sequence:
        raise ValueError("latest source_sequence required")
    if len(image_shape) != 3 or image_shape[2] != 3:
        raise ValueError("RGB source frame required")
    frame_height, frame_width, _ = image_shape
    target = _boxes(spec["target_boxes"], "target_boxes", frame_width, frame_height)
    guard = _boxes(spec["guard_boxes"], "guard_boxes", frame_width, frame_height)
    all_boxes = [("target", box) for box in target] + [("guard", box) for box in guard]
    for index, (role, box) in enumerate(all_boxes):
        if any(_overlap(box, other) for _, other in all_boxes[index + 1:]):
            raise ValueError(f"overlapping target/guard boxes are ambiguous ({role})")
    if type(spec["pixel_delta_threshold"]) is not int or not 1 <= spec["pixel_delta_threshold"] <= 255:
        raise ValueError("pixel_delta_threshold must be integer 1..255")
    target_area = sum(width * height for _, _, width, height in target)
    guard_area = sum(width * height for _, _, width, height in guard)
    if type(spec["minimum_target_changed_pixels"]) is not int or not 1 <= spec["minimum_target_changed_pixels"] <= target_area:
        raise ValueError("minimum_target_changed_pixels outside target area")
    if type(spec["maximum_guard_changed_pixels"]) is not int or not 0 <= spec["maximum_guard_changed_pixels"] < guard_area:
        raise ValueError("maximum_guard_changed_pixels outside guard area")
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


def _changed(source, sample, boxes, threshold):
    counts = []
    for x, y, width, height in boxes:
        left = source[y:y + height, x:x + width].astype(np.int16)
        right = sample[y:y + height, x:x + width].astype(np.int16)
        counts.append(int(np.count_nonzero(np.max(np.abs(left - right), axis=2) >= threshold)))
    return counts


class LocalTargetGuardPostcondition:
    def __init__(self, spec, source, source_sequence, binding):
        self.spec = validate(spec, source.shape, source_sequence)
        if not isinstance(binding, str) or not binding:
            raise ValueError("nonempty source binding required")
        self.source = np.asarray(source).copy()
        self.binding = binding

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
        if any(not isinstance(sample, np.ndarray) or sample.shape != self.source.shape for sample in samples):
            return self._outcome("frame_shape_changed", [], span_ms)
        threshold = self.spec["pixel_delta_threshold"]
        measurements = []
        for sample, sequence in zip(samples, sequences):
            target_counts = _changed(self.source, sample, self.spec["target_boxes"], threshold)
            guard_counts = _changed(self.source, sample, self.spec["guard_boxes"], threshold)
            measurements.append({
                "sequence": sequence,
                "target_changed_pixels": target_counts,
                "target_changed_total": sum(target_counts),
                "guard_changed_pixels": guard_counts,
                "guard_changed_total": sum(guard_counts),
            })
        if any(row["guard_changed_total"] > self.spec["maximum_guard_changed_pixels"]
               for row in measurements):
            reason = "guard_changed"
        elif any(row["target_changed_total"] < self.spec["minimum_target_changed_pixels"]
                 for row in measurements):
            reason = "target_not_reached"
        else:
            reason = "met"
        return self._outcome(reason, measurements, span_ms)

    def _outcome(self, reason, measurements, sample_span_ms):
        return {
            "format": "local-target-guard-postcondition-outcome-v1",
            "postcondition_id": self.spec["postcondition_id"],
            "reason": reason,
            "continue_program": reason == "met",
            "needs_decision": reason != "met",
            "measurements": measurements,
            "minimum_target_changed_pixels": self.spec["minimum_target_changed_pixels"],
            "maximum_guard_changed_pixels": self.spec["maximum_guard_changed_pixels"],
            "pixel_delta_threshold": self.spec["pixel_delta_threshold"],
            "sample_span_ms": sample_span_ms,
            "semantic_effect_verified": False,
            "task_success_verified": False,
            "grants_input_authority": False,
            "scope": "fixed-region visual condition for already admitted later steps only",
        }

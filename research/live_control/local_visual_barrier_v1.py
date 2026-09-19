"""Evaluate an agent-authored visual change barrier without semantic authority."""
from PIL import Image, ImageChops


FIELDS = {
    "op", "barrier_id", "source_sequence", "box", "metric", "rgb_threshold",
    "minimum_changed_pixels", "required_samples", "sample_interval_ms",
    "timeout_ms", "on_unmet",
}


def validate(spec, frame_size, current_sequence):
    if type(spec) is not dict or set(spec) != FIELDS:
        raise ValueError("exact local visual barrier fields required")
    if spec["op"] != "local_visual_barrier":
        raise ValueError("local_visual_barrier op required")
    if not isinstance(spec["barrier_id"], str) or not 1 <= len(spec["barrier_id"]) <= 64:
        raise ValueError("bounded barrier_id required")
    if type(spec["source_sequence"]) is not int or spec["source_sequence"] != current_sequence:
        raise ValueError("latest source_sequence required")
    if spec["metric"] != "persistent_rgb_change":
        raise ValueError("persistent_rgb_change metric required")
    box = spec["box"]
    if type(box) is not list or len(box) != 4 or any(type(value) is not int for value in box):
        raise ValueError("integer [left,top,right,bottom] box required")
    width, height = frame_size
    left, top, right, bottom = box
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError("barrier box outside source frame")
    pixels = (right - left) * (bottom - top)
    if pixels < 16 or pixels > 65536:
        raise ValueError("barrier box must contain 16..65536 pixels")
    if type(spec["rgb_threshold"]) is not int or not 1 <= spec["rgb_threshold"] <= 254:
        raise ValueError("rgb_threshold must be integer 1..254")
    if type(spec["minimum_changed_pixels"]) is not int or not 1 <= spec["minimum_changed_pixels"] <= pixels:
        raise ValueError("minimum_changed_pixels must fit the barrier box")
    if type(spec["required_samples"]) is not int or not 2 <= spec["required_samples"] <= 5:
        raise ValueError("required_samples must be integer 2..5")
    if type(spec["sample_interval_ms"]) is not int or not 20 <= spec["sample_interval_ms"] <= 500:
        raise ValueError("sample_interval_ms must be integer 20..500")
    if type(spec["timeout_ms"]) is not int or not 100 <= spec["timeout_ms"] <= 3000:
        raise ValueError("timeout_ms must be integer 100..3000")
    minimum_span = (spec["required_samples"] - 1) * spec["sample_interval_ms"]
    if minimum_span > spec["timeout_ms"]:
        raise ValueError("required samples do not fit timeout")
    if spec["on_unmet"] != "needs_decision":
        raise ValueError("unmet barrier must require a decision")
    return dict(spec)


class LocalVisualBarrier:
    def __init__(self, spec, source, source_sequence, binding):
        if not isinstance(source, Image.Image) or source.mode != "RGB":
            raise ValueError("RGB source image required")
        self.spec = validate(spec, source.size, source_sequence)
        if not isinstance(binding, str) or not binding:
            raise ValueError("nonempty source binding required")
        self.source = source.crop(self.spec["box"]).copy()
        self.frame_size = source.size
        self.binding = binding

    def evaluate(self, samples, bindings, sampled_ns):
        required = self.spec["required_samples"]
        if not (type(samples) is list and type(bindings) is list and type(sampled_ns) is list):
            raise ValueError("sample, binding and time lists required")
        if not len(samples) == len(bindings) == len(sampled_ns) == required:
            raise ValueError("exact required sample count required")
        if any(not isinstance(image, Image.Image) or image.mode != "RGB" or image.size != self.frame_size
               for image in samples):
            return self._outcome("invalid_frame", 0, None)
        if any(value != self.binding for value in bindings):
            return self._outcome("binding_changed", 0, None)
        if any(type(value) is not int or value <= 0 for value in sampled_ns):
            raise ValueError("positive integer sample times required")
        if sampled_ns != sorted(sampled_ns) or len(set(sampled_ns)) != len(sampled_ns):
            raise ValueError("strictly increasing sample times required")
        span_ms = (sampled_ns[-1] - sampled_ns[0]) / 1e6
        if span_ms > self.spec["timeout_ms"]:
            return self._outcome("timeout", 0, span_ms)
        masks = []
        for image in samples:
            difference = ImageChops.difference(self.source, image.crop(self.spec["box"]))
            masks.append([max(pixel) > self.spec["rgb_threshold"] for pixel in difference.getdata()])
        persistent = sum(all(mask[index] for mask in masks) for index in range(len(masks[0])))
        reason = "met" if persistent >= self.spec["minimum_changed_pixels"] else "unmet"
        return self._outcome(reason, persistent, span_ms)

    def _outcome(self, reason, persistent_pixels, sample_span_ms):
        return {
            "format": "local-visual-barrier-outcome-v1",
            "barrier_id": self.spec["barrier_id"],
            "reason": reason,
            "continue_program": reason == "met",
            "needs_decision": reason != "met",
            "persistent_changed_pixels": persistent_pixels,
            "minimum_changed_pixels": self.spec["minimum_changed_pixels"],
            "sample_span_ms": sample_span_ms,
            "semantic_effect_verified": False,
            "task_success_verified": False,
            "grants_input_authority": False,
            "scope": "condition for already admitted later steps only",
        }

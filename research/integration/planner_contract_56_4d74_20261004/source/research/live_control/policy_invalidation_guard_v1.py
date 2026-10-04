"""One-way visual invalidation for an already admitted local policy.

This deliberately cannot establish a postcondition or grant new input authority.
A matching sample merely leaves the existing policy unchanged; a changed or
unknown sample requires the caller to stop and obtain a new decision.
"""
from PIL import Image, ImageChops


FIELDS = {
    "op", "guard_id", "source_sequence", "box", "metric", "rgb_threshold",
    "minimum_changed_pixels", "max_source_age_ms", "on_change", "on_unknown",
}


def validate(spec, frame_size, current_sequence):
    if type(spec) is not dict or set(spec) != FIELDS:
        raise ValueError("exact policy invalidation guard fields required")
    if spec["op"] != "policy_invalidation_guard":
        raise ValueError("policy_invalidation_guard op required")
    if not isinstance(spec["guard_id"], str) or not 1 <= len(spec["guard_id"]) <= 64:
        raise ValueError("bounded guard_id required")
    if type(spec["source_sequence"]) is not int or spec["source_sequence"] != current_sequence:
        raise ValueError("latest source_sequence required")
    if spec["metric"] != "rgb_change":
        raise ValueError("rgb_change metric required")
    box = spec["box"]
    if type(box) is not list or len(box) != 4 or any(type(value) is not int for value in box):
        raise ValueError("integer [left,top,right,bottom] box required")
    width, height = frame_size
    left, top, right, bottom = box
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError("guard box outside source frame")
    pixels = (right - left) * (bottom - top)
    if pixels < 16 or pixels > 65536:
        raise ValueError("guard box must contain 16..65536 pixels")
    if type(spec["rgb_threshold"]) is not int or not 1 <= spec["rgb_threshold"] <= 254:
        raise ValueError("rgb_threshold must be integer 1..254")
    if (type(spec["minimum_changed_pixels"]) is not int or
            not 1 <= spec["minimum_changed_pixels"] <= pixels):
        raise ValueError("minimum_changed_pixels must fit the guard box")
    if (type(spec["max_source_age_ms"]) is not int or
            not 100 <= spec["max_source_age_ms"] <= 30000):
        raise ValueError("max_source_age_ms must be integer 100..30000")
    if spec["on_change"] != "needs_decision" or spec["on_unknown"] != "needs_decision":
        raise ValueError("changed and unknown outcomes must require a decision")
    return dict(spec)


class PolicyInvalidationGuard:
    def __init__(self, spec, source, source_sequence, binding, source_capture_ns):
        if not isinstance(source, Image.Image) or source.mode != "RGB":
            raise ValueError("RGB source image required")
        self.spec = validate(spec, source.size, source_sequence)
        if not isinstance(binding, str) or not binding:
            raise ValueError("nonempty source binding required")
        if type(source_capture_ns) is not int or source_capture_ns <= 0:
            raise ValueError("positive source_capture_ns required")
        self.source = source.crop(self.spec["box"]).copy()
        self.frame_size = source.size
        self.binding = binding
        self.source_capture_ns = source_capture_ns

    def evaluate(self, current, current_sequence, binding, sampled_ns):
        if not isinstance(current, Image.Image) or current.mode != "RGB" or current.size != self.frame_size:
            return self._outcome("UNKNOWN", "invalid_frame", 0, None)
        if binding != self.binding:
            return self._outcome("UNKNOWN", "binding_changed", 0, None)
        if type(current_sequence) is not int or current_sequence <= self.spec["source_sequence"]:
            return self._outcome("UNKNOWN", "nonadvancing_sequence", 0, None)
        if type(sampled_ns) is not int or sampled_ns <= self.source_capture_ns:
            return self._outcome("UNKNOWN", "invalid_sample_time", 0, None)
        age_ms = (sampled_ns - self.source_capture_ns) / 1e6
        if age_ms > self.spec["max_source_age_ms"]:
            return self._outcome("UNKNOWN", "source_expired", 0, age_ms)
        difference = ImageChops.difference(
            self.source, current.crop(self.spec["box"]))
        changed = sum(
            max(pixel) > self.spec["rgb_threshold"]
            for pixel in difference.getdata())
        if changed >= self.spec["minimum_changed_pixels"]:
            return self._outcome("INVALIDATED", "region_changed", changed, age_ms)
        return self._outcome("UNCHANGED", "below_change_threshold", changed, age_ms)

    def _outcome(self, status, reason, changed_pixels, source_age_ms):
        return {
            "format": "policy-invalidation-outcome-v1",
            "guard_id": self.spec["guard_id"],
            "status": status,
            "reason": reason,
            "keep_existing_policy": status == "UNCHANGED",
            "requires_new_decision": status != "UNCHANGED",
            "changed_pixels": changed_pixels,
            "minimum_changed_pixels": self.spec["minimum_changed_pixels"],
            "source_age_ms": source_age_ms,
            "grants_input_authority": False,
            "may_only_reduce_existing_authority": True,
            "semantic_change_identified": False,
            "task_success_verified": False,
        }

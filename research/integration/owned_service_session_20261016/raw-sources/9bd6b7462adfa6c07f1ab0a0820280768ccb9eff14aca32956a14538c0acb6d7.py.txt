"""Early in-memory and retained-file HUD extraction for one exact frame."""
from copy import deepcopy

import numpy as np
from PIL import Image

from doom_hud_signal_v2 import DoomStatusNumberReader as Previous


class DoomStatusNumberReader(Previous):
    """Add an in-memory path whose result is identical to the retained PNG path."""

    def read_frame(self, observation, frame):
        sequence = observation.get("sequence")
        capture_ns = observation.get("capture_ns")
        binding = observation.get("pointer_binding")
        if type(sequence) is not int or sequence < 0 or type(capture_ns) is not int or capture_ns <= 0:
            return self._unknown("invalid_observation_metadata", sequence, capture_ns, binding)
        if type(binding) is not dict or set(binding) != {"focus", "surface", "geometry"}:
            return self._unknown("invalid_binding", sequence, capture_ns, binding)
        geometry = binding.get("geometry")
        if (type(geometry) is not list or len(geometry) != 4 or
                any(type(value) is not int for value in geometry) or
                tuple(geometry[2:]) != self.client_size):
            return self._unknown("unsupported_geometry", sequence, capture_ns, binding)
        if not isinstance(frame, Image.Image):
            return self._unknown("frame_unavailable", sequence, capture_ns, binding)
        frame = frame.convert("RGB")
        left = geometry[0] + self.local_anchor[0]
        top = geometry[1] + self.local_anchor[1]
        width, height = self.glyph_size
        if (left < 0 or top < 0 or left + width * self.slots > frame.width or
                top + height > frame.height):
            return self._unknown("number_outside_frame", sequence, capture_ns, binding)
        number = np.asarray(frame.crop(
            (left, top, left + width * self.slots, top + height)))
        digits = []
        slots = []
        for index in range(self.slots):
            crop = number[:, index * width:(index + 1) * width]
            scores = []
            for template, mask in self.templates:
                exact = np.all(crop == template, axis=2)
                scores.append(float(exact[mask].mean()))
            order = sorted(range(10), key=scores.__getitem__, reverse=True)
            best, second = order[:2]
            if scores[best] < self.minimum_score:
                digit = None
            elif scores[best] - scores[second] < self.minimum_margin:
                return self._unknown("ambiguous_digit", sequence, capture_ns, binding,
                                     {"slot": index, "scores": scores})
            else:
                digit = best
            slots.append({"slot": index, "digit": digit, "best_digit": best,
                          "best_score": scores[best], "second_score": scores[second]})
            digits.append(digit)
        first = next((index for index, digit in enumerate(digits) if digit is not None), None)
        if first is None or any(digit is None for digit in digits[first:]) or any(
                digit is not None for digit in digits[:first]):
            return self._unknown("invalid_right_aligned_number", sequence, capture_ns, binding,
                                 {"slots": slots})
        value = int("".join(str(digit) for digit in digits[first:]))
        return {
            "format": "observable-signal-v1", "status": "observed",
            "signal_id": self.signal_id, "value": value,
            "sequence": sequence, "capture_ns": capture_ns,
            "binding": deepcopy(binding), "slots": slots,
            "evidence": "hash-bound WAD glyph foreground exact-match",
            "wad_sha256": self.wad_sha256,
        }

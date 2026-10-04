"""Hash-bound Freedoom status-number extraction from exact X11 observations."""
import hashlib
from pathlib import Path
import struct

import numpy as np
from PIL import Image


FREEDOOM2_SHA256 = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _wad_lumps(path, expected_sha256):
    path = Path(path)
    if sha256(path) != expected_sha256:
        raise ValueError("WAD hash mismatch")
    data = path.read_bytes()
    if len(data) < 12:
        raise ValueError("truncated WAD")
    identifier, count, directory = struct.unpack_from("<4sII", data, 0)
    if identifier not in (b"IWAD", b"PWAD") or count > 1_000_000:
        raise ValueError("invalid WAD header")
    if directory + count * 16 > len(data):
        raise ValueError("invalid WAD directory")
    lumps = {}
    for index in range(count):
        offset, size, raw_name = struct.unpack_from("<II8s", data, directory + index * 16)
        if offset + size > len(data):
            raise ValueError("invalid WAD lump bounds")
        name = raw_name.rstrip(b"\0").decode("ascii", "strict")
        lumps[name] = data[offset:offset + size]
    return lumps


def _render_patch(data, palette):
    if len(data) < 8:
        raise ValueError("truncated Doom patch")
    width, height, _, _ = struct.unpack_from("<hhhh", data, 0)
    if not (1 <= width <= 512 and 1 <= height <= 512 and 8 + width * 4 <= len(data)):
        raise ValueError("invalid Doom patch geometry")
    indices = np.zeros((height, width), dtype=np.uint8)
    alpha = np.zeros((height, width), dtype=np.uint8)
    for x in range(width):
        cursor = struct.unpack_from("<I", data, 8 + x * 4)[0]
        posts = 0
        while True:
            if cursor >= len(data):
                raise ValueError("invalid Doom patch column")
            top = data[cursor]
            if top == 255:
                break
            if cursor + 4 > len(data):
                raise ValueError("truncated Doom patch post")
            length = data[cursor + 1]
            start = cursor + 3
            end = start + length
            if end + 1 > len(data) or top + length > height:
                raise ValueError("invalid Doom patch post bounds")
            indices[top:top + length, x] = np.frombuffer(data[start:end], dtype=np.uint8)
            alpha[top:top + length, x] = 255
            cursor = end + 1
            posts += 1
            if posts > height:
                raise ValueError("excess Doom patch posts")
    rgb = palette[indices]
    return np.dstack((rgb, alpha))


class DoomStatusNumberReader:
    """Read a right-aligned three-slot status number using WAD glyph evidence."""

    def __init__(self, wad_path, signal_id="health", local_anchor=(102, 411),
                 client_size=(640, 480), slots=3, glyph_size=(26, 38),
                 minimum_score=0.80, minimum_margin=0.05,
                 expected_wad_sha256=FREEDOOM2_SHA256, image_resolver=None):
        if signal_id != "health":
            raise ValueError("validated health signal_id required")
        if (type(local_anchor) is not tuple or len(local_anchor) != 2 or
                any(type(value) is not int for value in local_anchor)):
            raise ValueError("integer local_anchor required")
        if client_size != (640, 480) or slots != 3 or glyph_size != (26, 38):
            raise ValueError("frozen MAP01 HUD geometry required")
        if not (0.5 <= minimum_score <= 1 and 0 <= minimum_margin <= 0.5):
            raise ValueError("bounded matching thresholds required")
        lumps = _wad_lumps(wad_path, expected_wad_sha256)
        if "PLAYPAL" not in lumps or len(lumps["PLAYPAL"]) < 768:
            raise ValueError("PLAYPAL palette required")
        palette = np.frombuffer(lumps["PLAYPAL"][:768], dtype=np.uint8).reshape(256, 3)
        self.templates = []
        for digit in range(10):
            name = f"STTNUM{digit}"
            if name not in lumps:
                raise ValueError(f"{name} patch required")
            patch = Image.fromarray(_render_patch(lumps[name], palette))
            resized = np.asarray(patch.resize(glyph_size, Image.Resampling.NEAREST))
            self.templates.append((resized[:, :, :3], resized[:, :, 3] > 0))
        self.wad_sha256 = expected_wad_sha256
        self.signal_id = signal_id
        self.local_anchor = local_anchor
        self.client_size = client_size
        self.slots = slots
        self.glyph_size = glyph_size
        self.minimum_score = minimum_score
        self.minimum_margin = minimum_margin
        self.image_resolver = image_resolver or Path

    def read(self, observation):
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
        left = geometry[0] + self.local_anchor[0]
        top = geometry[1] + self.local_anchor[1]
        width, height = self.glyph_size
        try:
            with Image.open(self.image_resolver(observation["image"])) as opened:
                frame = opened.convert("RGB")
                if (left < 0 or top < 0 or left + width * self.slots > frame.width or
                        top + height > frame.height):
                    return self._unknown("number_outside_frame", sequence, capture_ns, binding)
                number = np.asarray(frame.crop(
                    (left, top, left + width * self.slots, top + height)))
        except (KeyError, OSError, ValueError):
            return self._unknown("image_unavailable", sequence, capture_ns, binding)
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
            "binding": binding, "slots": slots,
            "evidence": "hash-bound WAD glyph foreground exact-match",
            "wad_sha256": self.wad_sha256,
        }

    def _unknown(self, reason, sequence, capture_ns, binding, detail=None):
        row = {
            "format": "observable-signal-v1", "status": "unknown",
            "reason": reason, "signal_id": self.signal_id,
            "value": None, "sequence": sequence, "capture_ns": capture_ns,
            "binding": binding, "wad_sha256": self.wad_sha256,
        }
        if detail is not None:
            row["detail"] = detail
        return row

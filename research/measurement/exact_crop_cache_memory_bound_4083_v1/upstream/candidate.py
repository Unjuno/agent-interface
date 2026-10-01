"""Research-only dependency-closed cache for exact_crop_semantic_probe_v1.

This is not a runtime patch. It reuses only nodes keyed by exact artifact bytes
and exact ROI, while delegating contract validation and frame digest semantics to
the frozen upstream implementation.
"""
from io import BytesIO
from pathlib import Path
import hashlib
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "upstream"))
import exact_crop_semantic_probe_v1 as upstream
from inkscape_selection_frame_probe_v1 import ExactFrame, frame_sha256


class DependencyCache:
    def __init__(self):
        self.frames = {}
        self.crops = {}
        self.counters = {
            "artifact_version_checks": 0,
            "frame_recompute": 0,
            "frame_reuse": 0,
            "crop_recompute": 0,
            "crop_reuse": 0,
        }

    @staticmethod
    def _decode(raw):
        with Image.open(BytesIO(raw)) as source:
            image = source.convert("RGB")
            return ExactFrame(image.width, image.height, image.mode, image.tobytes())

    def score(self, contract, image_path):
        contract = upstream.validate(contract)
        raw = Path(image_path).read_bytes()
        self.counters["artifact_version_checks"] += 1
        artifact_sha = hashlib.sha256(raw).hexdigest()
        cached = self.frames.get(artifact_sha)
        if cached is None:
            frame = self._decode(raw)
            cached = (frame, frame_sha256(frame))
            self.frames[artifact_sha] = cached
            self.counters["frame_recompute"] += 1
        else:
            self.counters["frame_reuse"] += 1
        frame, frame_sha = cached
        if frame.mode != "RGB" or len(frame.pixels) != frame.width * frame.height * 3:
            raise ValueError("valid RGB exact frame required")
        left, top, right, bottom = contract["box"]
        if right > frame.width or bottom > frame.height:
            raise ValueError("crop outside exact frame")
        crop_key = (artifact_sha, left, top, right, bottom)
        observed = self.crops.get(crop_key)
        if observed is None:
            pixels = np.frombuffer(frame.pixels, dtype=np.uint8).reshape(frame.height, frame.width, 3)
            observed = hashlib.sha256(pixels[top:bottom, left:right].tobytes()).hexdigest()
            self.crops[crop_key] = observed
            self.counters["crop_recompute"] += 1
        else:
            self.counters["crop_reuse"] += 1
        success = observed == contract["expected_crop_sha256"]
        return {
            "schema": upstream.SCORE_SCHEMA,
            "probe_id": contract["probe_id"],
            "success": success,
            "reason": contract["success_reason"] if success else "expected_crop_missing",
            "box": list(contract["box"]),
            "observed_crop_sha256": observed,
            "expected_crop_sha256": contract["expected_crop_sha256"],
            "scored_frame_sha256": frame_sha,
            "frame": {"width": frame.width, "height": frame.height, "mode": frame.mode},
            "grants_input_authority": False,
        }

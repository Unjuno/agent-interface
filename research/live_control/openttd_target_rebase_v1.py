"""Bind hover-selected meaning back to a persistent pre-hover target patch."""
import hashlib
from pathlib import Path

from PIL import Image

from model_point_target_v1 import derive, patch


def image(path):
    with Image.open(Path(path)) as opened:
        return opened.convert("RGB")


def verify(source_observation, source_image, current_observation, current_image,
           point, region_size):
    if (source_observation.get("pointer_binding")
            != current_observation.get("pointer_binding")):
        raise ValueError("binding changed before target rebase")
    if (source_observation.get("focus_samples_match") is not True
            or current_observation.get("focus_samples_match") is not True):
        raise ValueError("focus samples changed before target rebase")
    derived = derive(point, region_size)
    source_pixels = patch(image(source_image), derived["box"])
    current_pixels = patch(image(current_image), derived["box"])
    if source_pixels != current_pixels:
        raise ValueError("persistent pre-hover target patch not restored")
    digest = hashlib.sha256(source_pixels).hexdigest()
    return {"status": "REBASABLE", "point": point, "region_size": region_size,
            "box": derived["box"], "offset": derived["offset"],
            "source_sequence": source_observation["sequence"],
            "current_sequence": current_observation["sequence"],
            "patch_sha256": digest,
            "authority": "readiness evidence only; grants no input authority"}

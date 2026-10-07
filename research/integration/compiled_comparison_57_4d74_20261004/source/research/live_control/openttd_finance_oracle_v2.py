"""Score the OpenTTD finance title after an observed whole-surface translation."""
import hashlib
from pathlib import Path

from PIL import Image

from openttd_finance_oracle_v1 import EXPECTED_TITLE_SHA256, TITLE_BOX


def shifted_box(delta):
    if (not isinstance(delta, (list, tuple)) or len(delta) != 2
            or type(delta[0]) is not int or type(delta[1]) is not int):
        raise ValueError("integer surface delta required")
    dx, dy = delta
    return [TITLE_BOX[0] + dx, TITLE_BOX[1] + dy,
            TITLE_BOX[2] + dx, TITLE_BOX[3] + dy]


def score(image_or_path, delta):
    if isinstance(image_or_path, Image.Image):
        image = image_or_path.convert("RGB")
    else:
        with Image.open(Path(image_or_path)) as opened:
            image = opened.convert("RGB")
    box = shifted_box(delta)
    if box[0] < 0 or box[1] < 0 or box[2] > image.width or box[3] > image.height:
        raise ValueError("translated finance-title region outside image")
    digest = hashlib.sha256(image.crop(tuple(box)).tobytes()).hexdigest()
    return {"success": digest == EXPECTED_TITLE_SHA256,
            "surface_delta": list(delta), "title_box": box,
            "observed_title_sha256": digest,
            "expected_title_sha256": EXPECTED_TITLE_SHA256,
            "basis": "observed whole-surface delta plus exact fixed-seed RGB title crop"}

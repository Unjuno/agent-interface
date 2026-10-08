"""Independent fixed-seed visual oracle for the OpenTTD company-finances window."""
import hashlib
from pathlib import Path

from PIL import Image


TITLE_BOX = (143, 64, 497, 78)
EXPECTED_TITLE_SHA256 = "c1f9c04420415093ce46fad515e9e712b2976ddfa2df745a6af224755b593fc0"


def score(image_or_path):
    if isinstance(image_or_path, Image.Image):
        image = image_or_path.convert("RGB")
    else:
        with Image.open(Path(image_or_path)) as opened:
            image = opened.convert("RGB")
    if image.width < TITLE_BOX[2] or image.height < TITLE_BOX[3]:
        raise ValueError("image is smaller than the fixed finance-title region")
    digest = hashlib.sha256(image.crop(TITLE_BOX).tobytes()).hexdigest()
    return {
        "success": digest == EXPECTED_TITLE_SHA256,
        "title_box": list(TITLE_BOX),
        "observed_title_sha256": digest,
        "expected_title_sha256": EXPECTED_TITLE_SHA256,
        "basis": "fixed-seed exact RGB title crop; independent of model decision",
    }

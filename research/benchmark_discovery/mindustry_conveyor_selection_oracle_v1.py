"""Exact visual oracle for the fixed Mindustry Conveyor selection UI state."""
import hashlib
from pathlib import Path

from PIL import Image


REFERENCE = Path(__file__).resolve().parent / "results/mindustry-bend-v2-self-use-01/004.png"
REFERENCE_SHA256 = "9e0850be0d53b7c3ce3d3e0f7ec737418c4151b92eb6d123d8f0dd4fc97e4fc6"
TITLE_BOX = [967, 447, 1280, 547]
SLOT_BOX = [987, 557, 1032, 603]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def crop_sha(path, box):
    with Image.open(path) as opened:
        return hashlib.sha256(opened.convert("RGB").crop(tuple(box)).tobytes()).hexdigest()


def score(image_path):
    if sha(REFERENCE) != REFERENCE_SHA256:
        raise ValueError("pinned Mindustry selection reference changed")
    expected_title = crop_sha(REFERENCE, TITLE_BOX)
    expected_slot = crop_sha(REFERENCE, SLOT_BOX)
    observed_title = crop_sha(image_path, TITLE_BOX)
    observed_slot = crop_sha(image_path, SLOT_BOX)
    return {"success": observed_title == expected_title and observed_slot == expected_slot,
            "title_box": TITLE_BOX, "slot_box": SLOT_BOX,
            "observed_title_sha256": observed_title,
            "expected_title_sha256": expected_title,
            "observed_slot_sha256": observed_slot,
            "expected_slot_sha256": expected_slot,
            "basis": "exact fixed-fixture RGB title panel plus selected Conveyor slot border"}

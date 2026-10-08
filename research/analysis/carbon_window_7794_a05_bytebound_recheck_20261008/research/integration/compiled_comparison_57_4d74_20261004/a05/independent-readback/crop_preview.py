"""Render reproducible crop previews for the three retained C-arm failures.

This is visual crop geometry evidence only. It does not run OCR or the study.
Requires Pillow, which is already a dependency of the pinned A05 adapter.
"""
import hashlib
import io
import json
import subprocess
from pathlib import Path

from PIL import Image

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
REF = "58bcbb4c45501880db8782158ddd3add3b765984"
BASE = "research/integration/compiled_comparison_57_4d74_20261004/a05/formal-output"
OUT = Path(__file__).with_name("crop-previews")
FROZEN_BOX = (499, 544, 799, 573)
CANDIDATE_BOX = (493, 539, 805, 579)
CASES = (
    (1, 5, 124, "4abaa062c4a73c7d739fe6bfef856ae37f6f0bda5326732a764183c67b7ab9cd"),
    (1, 6, 143, "2fce53c538dca90012952147a20ef0efd7b0ead6e067971778e12fed0caf6b26"),
    (2, 6, 150, "166cd642ffe36474773d592118ddcd08c0202ce722948bdc1747068a02e262f5"),
)


def git_show(path):
    return subprocess.check_output(["git", "-C", REPO, "show", f"{REF}:{path}"])


OUT.mkdir(exist_ok=True)
entries = []
for block, task, sequence, expected_source_sha in CASES:
    source_path = f"{BASE}/block-{block}/C/client/runtime/{sequence:03d}.png"
    source = git_show(source_path)
    source_sha = hashlib.sha256(source).hexdigest()
    assert source_sha == expected_source_sha, (source_path, source_sha)
    with Image.open(io.BytesIO(source)) as img:
        frame = img.convert("RGB")
    gray = frame.convert("L")
    input_edge_rows = [
        y for y in range(538, 580)
        if sum(gray.getpixel((x, y)) < 90 for x in range(480, 820)) >= 280
    ]
    input_edge_columns = [
        x for x in range(480, 820)
        if sum(gray.getpixel((x, y)) < 90 for y in range(538, 580)) >= 25
    ]
    assert input_edge_rows == [541, 542, 575, 576], (source_path, input_edge_rows)
    assert input_edge_columns == [495, 496, 801, 802], (source_path, input_edge_columns)
    detected_field_box = (min(input_edge_columns), min(input_edge_rows),
                          max(input_edge_columns) + 1, max(input_edge_rows) + 1)
    assert not (FROZEN_BOX[0] <= detected_field_box[0]
                and FROZEN_BOX[1] <= detected_field_box[1]
                and FROZEN_BOX[2] >= detected_field_box[2]
                and FROZEN_BOX[3] >= detected_field_box[3])
    assert (CANDIDATE_BOX[0] <= detected_field_box[0]
            and CANDIDATE_BOX[1] <= detected_field_box[1]
            and CANDIDATE_BOX[2] >= detected_field_box[2]
            and CANDIDATE_BOX[3] >= detected_field_box[3])
    if FROZEN_BOX[2] > frame.width or FROZEN_BOX[3] > frame.height:
        raise ValueError(f"frozen crop outside {source_path}")
    if CANDIDATE_BOX[2] > frame.width or CANDIDATE_BOX[3] > frame.height:
        raise ValueError(f"candidate crop outside {source_path}")

    for label, box in (("frozen", FROZEN_BOX), ("candidate", CANDIDATE_BOX)):
        crop = frame.crop(box)
        crop = crop.resize((crop.width * 4, crop.height * 4))
        name = f"block-{block}-task-{task}-{label}.png"
        target = OUT / name
        crop.save(target, format="PNG")
        preview_bytes = target.read_bytes()
        entries.append({
            "block": block,
            "task": task,
            "crop": label,
            "source_revision": REF,
            "source_path": source_path,
            "source_sha256": source_sha,
            "box_xyxy": list(box),
            "detected_field_box_xyxy": list(detected_field_box),
            "crop_contains_detected_field": (
                box[0] <= detected_field_box[0]
                and box[1] <= detected_field_box[1]
                and box[2] >= detected_field_box[2]
                and box[3] >= detected_field_box[3]
            ),
            "scale": 4,
            "output": f"crop-previews/{name}",
            "output_size": list(crop.size),
            "output_sha256": hashlib.sha256(preview_bytes).hexdigest(),
        })

manifest = {
    "purpose": "Reproduce the exact frozen and padded crop previews used for visual diagnosis of the three C-arm OCR false negatives.",
    "source_revision": REF,
    "ocr_executed": False,
    "field_edge_detection": "dark horizontal/vertical border pixels in the fixed ROI; thresholded for these pinned fixture frames",
    "frozen_box_xyxy": list(FROZEN_BOX),
    "candidate_box_xyxy": list(CANDIDATE_BOX),
    "entries": entries,
}
manifest_path = OUT / "manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(manifest, indent=2, sort_keys=True))

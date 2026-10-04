"""Replay pinned layout-B crop OCR locally; never starts the study or a GUI."""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

SOURCE_REVISION = "58bcbb4c45501880db8782158ddd3add3b765984"
BASE = "research/integration/compiled_comparison_57_4d74_20261004/a05/formal-output"
FROZEN_BOX = (499, 544, 799, 573)
CANDIDATE_BOX = (493, 539, 805, 579)
CASES = (
    {
        "id": "failure-b1-t5",
        "block": 1,
        "task": 5,
        "sequence": 124,
        "expected": "t991073-5",
        "near_miss": "t991073-0",
        "original_recorded_ocr": "991073-5\n",
        "source_sha256": "4abaa062c4a73c7d739fe6bfef856ae37f6f0bda5326732a764183c67b7ab9cd",
    },
    {
        "id": "failure-b1-t6",
        "block": 1,
        "task": 6,
        "sequence": 143,
        "expected": "t991073-6",
        "near_miss": "t991073-0",
        "original_recorded_ocr": "991073-6\n",
        "source_sha256": "2fce53c538dca90012952147a20ef0efd7b0ead6e067971778e12fed0caf6b26",
    },
    {
        "id": "failure-b2-t6",
        "block": 2,
        "task": 6,
        "sequence": 150,
        "expected": "t991074-6",
        "near_miss": "t991074-0",
        "original_recorded_ocr": "991074-6\n",
        "source_sha256": "166cd642ffe36474773d592118ddcd08c0202ce722948bdc1747068a02e262f5",
    },
    {
        "id": "positive-nearmiss-control-b1-t4",
        "block": 1,
        "task": 4,
        "sequence": 99,
        "expected": "t991073-4",
        "near_miss": "t991073-5",
        "original_recorded_ocr": "t991073-4\n",
        "source_sha256": "430b107eee1172c512e6163a3c0c41f959259a3518880da611715824698af301",
    },
)
OCR_ARGS = (
    "stdout",
    "--psm",
    "7",
    "-c",
    "tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789-",
)


def source_bytes(path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{SOURCE_REVISION}:{path}"]
    )


def main() -> dict:
    tesseract = shutil.which("tesseract")
    if not tesseract:
        raise RuntimeError("tesseract executable is unavailable")
    version = subprocess.check_output([tesseract, "--version"], text=True).splitlines()[0]
    languages = subprocess.check_output([tesseract, "--list-langs"], text=True)
    if "\neng\n" not in f"\n{languages}\n":
        raise RuntimeError("English traineddata is unavailable")

    rows = []
    with tempfile.TemporaryDirectory(prefix="a09-layout-b-ocr-") as temp_dir:
        for case in CASES:
            source_path = (
                f"{BASE}/block-{case['block']}/C/client/runtime/"
                f"{case['sequence']:03d}.png"
            )
            source = source_bytes(source_path)
            source_sha = hashlib.sha256(source).hexdigest()
            if source_sha != case["source_sha256"]:
                raise ValueError((case["id"], "source hash mismatch", source_sha))
            with Image.open(io.BytesIO(source)) as image_file:
                image = image_file.convert("RGB")

            crop_results = []
            for label, box in (("frozen", FROZEN_BOX), ("candidate", CANDIDATE_BOX)):
                crop = image.crop(box)
                crop = crop.resize((crop.width * 4, crop.height * 4))
                crop_path = Path(temp_dir) / f"{case['id']}-{label}.png"
                crop.save(crop_path, format="PNG")
                crop_bytes = crop_path.read_bytes()
                started_ns = time.perf_counter_ns()
                result = subprocess.run(
                    [tesseract, str(crop_path), *OCR_ARGS],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                elapsed_ns = time.perf_counter_ns() - started_ns
                output = result.stdout.strip()
                crop_results.append(
                    {
                        "crop": label,
                        "box_xyxy": list(box),
                        "crop_sha256": hashlib.sha256(crop_bytes).hexdigest(),
                        "ocr_exit": result.returncode,
                        "ocr_stdout": result.stdout,
                        "ocr_stderr": result.stderr,
                        "ocr_elapsed_ns": elapsed_ns,
                        "matches_expected": result.returncode == 0 and output == case["expected"],
                        "near_miss": case["near_miss"],
                        "rejects_near_miss": result.returncode == 0 and output != case["near_miss"],
                    }
                )
            rows.append(
                {
                    **case,
                    "source_path": source_path,
                    "source_sha256": source_sha,
                    "crop_results": crop_results,
                }
            )

    return {
        "schema": "a09_layout_b_ocr_backend_reproduction_v1",
        "source_revision": SOURCE_REVISION,
        "tesseract_path": tesseract,
        "tesseract_version": version,
        "available_languages_output": languages,
        "language": "eng",
        "command": ["tesseract", "<crop.png>", *OCR_ARGS],
        "crop_scale": 4,
        "rows": rows,
        "scope": "read-only local replay of pinned screenshots and crop geometry; no provider, GUI, input, formal allocation, or study runner",
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))

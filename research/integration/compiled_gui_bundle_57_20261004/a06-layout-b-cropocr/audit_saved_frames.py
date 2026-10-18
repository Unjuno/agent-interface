"""Audit the retained layout-B blank/entered screenshots with the v2 crop."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

from PIL import __version__ as pillow_version

from adapter import read_crop_token


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
FRAME_ROOT = (
    REPO_ROOT
    / "research/live_control/results/integrated-efficiency-live-orchestration-probe-02"
    / "arms/ephemeral/runtime"
)
EXPECTED = {
    "068.png": None,
    "077.png": "t991028-4",
    "093.png": None,
    "100.png": "t991028-5",
    "115.png": None,
    "121.png": "t991028-6",
}
EXPECTED_SHA256 = {
    "068.png": "e1416a9e8e5c084dbc888af20f7d43c2475163fe01879ebd748bb4c4ac71ad2f",
    "077.png": "f07a6655e0f633db72a37450690282704cfa490aa2feb8f8e36c2524d4e8a185",
    "093.png": "fb66e465daa52f78dfd34b10d51f3afefb1c1f08691c13605d3d20fdc34ff143",
    "100.png": "4c783c14eb9be98ce36119f338d3f76505b4e71953786a7a53ca8ac7888188c5",
    "115.png": "b44309dec6b19a13e9aad0578d1dae5143c0c27883190e70b50681644f435843",
    "121.png": "df091f2154717c726740ea9a5f0c22b2f88a6c8ced35cb24752450d95dc68961",
}
TOKEN_PATTERN = re.compile(r"^t\d{6}-\d$")
BLANK_SENTINEL = "__NO_EXPECTED_TOKEN__"


def audit_saved_frames(
    *, tesseract: str = "tesseract", runner: Callable = subprocess.run
) -> dict:
    version = runner(
        [tesseract, "--version"], capture_output=True, text=True, timeout=5, check=False
    )
    version_text = (version.stdout or "").splitlines()
    if version.returncode != 0 or not version_text or version_text[0] != "tesseract 5.5.0":
        raise ValueError("Tesseract 5.5.0 required for this pinned diagnostic")
    if not any("leptonica-1.84.1" in line for line in version_text[1:2]):
        raise ValueError("Leptonica 1.84.1 required for this pinned diagnostic")

    rows = []
    with tempfile.TemporaryDirectory(prefix="layout-b-cropocr-") as temp_dir:
        temporary_root = Path(temp_dir)
        for filename, expected in EXPECTED.items():
            frame = FRAME_ROOT / filename
            digest = hashlib.sha256(frame.read_bytes()).hexdigest()
            if digest != EXPECTED_SHA256[filename]:
                raise ValueError(f"source frame hash mismatch: {filename}")
            result = read_crop_token(
                frame,
                "B",
                expected if expected is not None else BLANK_SENTINEL,
                temporary_root / (frame.stem + "-crop.png"),
                tesseract=tesseract,
                runner=runner,
            )
            if result["status"] != "completed":
                raise ValueError(f"OCR failed on {filename}: {result['stderr']}")
            if expected is not None and result["exact"] is not True:
                raise ValueError(f"expected token mismatch on {filename}")
            if expected is None and TOKEN_PATTERN.fullmatch(result["stdout"].strip()):
                raise ValueError(f"blank frame produced a token-shaped false positive: {filename}")
            rows.append(
                {
                    "frame": filename,
                    "sha256": digest,
                    "expected": expected,
                    "ocr_stdout": result["stdout"],
                    "exact": result["exact"],
                    "crop_sha256": result["crop_sha256"],
                }
            )

    return {
        "status": "PASS_LAYOUT_B_FIT_ONLY",
        "tesseract_version": version_text[0],
        "leptonica_version": version_text[1].strip(),
        "pillow_version": pillow_version,
        "layout": "B",
        "crop_box_xyxy": [495, 541, 803, 577],
        "crop_output_size": [1848, 216],
        "resampling": "Lanczos",
        "psm": 7,
        "filled_exact": sum(row["exact"] is True for row in rows),
        "filled_total": sum(row["expected"] is not None for row in rows),
        "blank_token_false_positives": sum(
            row["expected"] is None and bool(TOKEN_PATTERN.fullmatch(row["ocr_stdout"].strip()))
            for row in rows
        ),
        "blank_total": sum(row["expected"] is None for row in rows),
        "formal_comparison_credit": False,
        "frames": rows,
    }


def main() -> int:
    try:
        result = audit_saved_frames()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

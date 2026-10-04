"""Independent readback and OCR rerun for A09's captured raw record."""

from __future__ import annotations

import importlib.util
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


RUNNER = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("a09_run", RUNNER)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load pinned A09 case definition")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def main(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    checks = []
    problems = []
    if raw.get("schema") != "a09_layout_b_ocr_backend_reproduction_v1":
        problems.append("unexpected schema")
    if raw.get("source_revision") != MODULE.SOURCE_REVISION:
        problems.append("source revision mismatch")
    if len(raw.get("rows", [])) != len(MODULE.CASES):
        problems.append("case count mismatch")

    for expected_case, row in zip(MODULE.CASES, raw.get("rows", []), strict=False):
        case_id = expected_case["id"]
        if row.get("id") != case_id:
            problems.append(f"case ordering/id mismatch: {case_id}")
            continue
        if row.get("source_sha256") != expected_case["source_sha256"]:
            problems.append(f"source hash mismatch: {case_id}")
        for crop_name, box in (("frozen", MODULE.FROZEN_BOX), ("candidate", MODULE.CANDIDATE_BOX)):
            crop = next((item for item in row.get("crop_results", []) if item.get("crop") == crop_name), None)
            if crop is None:
                problems.append(f"missing {crop_name} result: {case_id}")
                continue
            if crop.get("box_xyxy") != list(box):
                problems.append(f"crop bounds mismatch: {case_id}/{crop_name}")
            output = crop.get("ocr_stdout", "").strip()
            expected = expected_case["expected"]
            near_miss = expected_case["near_miss"]
            actual_exact = crop.get("ocr_exit") == 0 and output == expected
            actual_reject = crop.get("ocr_exit") == 0 and output != near_miss
            if crop.get("matches_expected") != actual_exact:
                problems.append(f"exact-match audit disagreement: {case_id}/{crop_name}")
            if crop.get("rejects_near_miss") != actual_reject:
                problems.append(f"near-miss audit disagreement: {case_id}/{crop_name}")
            checks.append(
                {
                    "case": case_id,
                    "crop": crop_name,
                    "exact_expected": actual_exact,
                    "near_miss_rejected": actual_reject,
                    "crop_sha256": crop.get("crop_sha256"),
                }
            )

    # Rebuild the crop inputs with this separate implementation, then rerun OCR.
    tesseract = shutil.which("tesseract")
    if not tesseract:
        problems.append("tesseract executable is unavailable for independent replay")
    else:
        with tempfile.TemporaryDirectory(prefix="a09-independent-audit-") as temp_dir:
            for expected_case, raw_row in zip(MODULE.CASES, raw.get("rows", []), strict=False):
                source_path = (
                    f"{MODULE.BASE}/block-{expected_case['block']}/C/client/runtime/"
                    f"{expected_case['sequence']:03d}.png"
                )
                source = subprocess.check_output(
                    ["git", "show", f"{MODULE.SOURCE_REVISION}:{source_path}"]
                )
                source_digest = hashlib.sha256(source).hexdigest()
                if source_digest != raw_row.get("source_sha256"):
                    problems.append(f"independent source replay mismatch: {expected_case['id']}")
                with Image.open(io.BytesIO(source)) as opened:
                    rgb = opened.convert("RGB")
                for crop_name, bounds in (("frozen", MODULE.FROZEN_BOX), ("candidate", MODULE.CANDIDATE_BOX)):
                    crop = rgb.crop(bounds)
                    crop = crop.resize((4 * crop.width, 4 * crop.height))
                    crop_path = Path(temp_dir) / f"{expected_case['id']}-{crop_name}.png"
                    crop.save(crop_path, format="PNG")
                    crop_digest = hashlib.sha256(crop_path.read_bytes()).hexdigest()
                    command = [
                        tesseract,
                        str(crop_path),
                        "stdout",
                        "--psm",
                        "7",
                        "-c",
                        "tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789-",
                    ]
                    result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
                    raw_crop = next(
                        (item for item in raw_row.get("crop_results", []) if item.get("crop") == crop_name),
                        None,
                    )
                    key = (expected_case["id"], crop_name)
                    if raw_crop is None:
                        problems.append(f"missing raw crop during replay: {key}")
                        continue
                    for field, replay_value in (
                        ("crop_sha256", crop_digest),
                        ("ocr_exit", result.returncode),
                        ("ocr_stdout", result.stdout),
                    ):
                        if replay_value != raw_crop.get(field):
                            problems.append(f"independent OCR replay mismatch: {key}/{field}")

    failure_rows = [row for row in raw.get("rows", []) if row.get("id", "").startswith("failure-")]
    frozen_exact = sum(
        item.get("matches_expected") is True
        for row in failure_rows
        for item in row.get("crop_results", [])
        if item.get("crop") == "frozen"
    )
    candidate_exact = sum(
        item.get("matches_expected") is True
        for row in failure_rows
        for item in row.get("crop_results", [])
        if item.get("crop") == "candidate"
    )
    control = next((row for row in raw.get("rows", []) if row.get("id") == "positive-nearmiss-control-b1-t4"), None)
    disposition = (
        "UNCERTAIN_HISTORICAL_FALSE_NEGATIVE_NOT_REPRODUCED"
        if frozen_exact == candidate_exact == 3
        else "HOLD_REVIEW_REQUIRED"
    )
    report = {
        "schema": "a09_layout_b_ocr_backend_reproduction_audit_v1",
        "raw_sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
        "independent_replay": "PASS" if not problems else "FAIL",
        "checks": checks,
        "failure_frame_exact_counts": {"frozen": frozen_exact, "candidate": candidate_exact, "n": len(failure_rows)},
        "task4_control": {
            "near_miss_token": "t991073-5",
            "frozen_exact": next((x.get("matches_expected") for x in control.get("crop_results", []) if x.get("crop") == "frozen"), None) if control else None,
            "candidate_exact": next((x.get("matches_expected") for x in control.get("crop_results", []) if x.get("crop") == "candidate"), None) if control else None,
            "frozen_near_miss_rejected": next((x.get("rejects_near_miss") for x in control.get("crop_results", []) if x.get("crop") == "frozen"), None) if control else None,
            "candidate_near_miss_rejected": next((x.get("rejects_near_miss") for x in control.get("crop_results", []) if x.get("crop") == "candidate"), None) if control else None,
        },
        "disposition": disposition,
        "formal_a05_result_changed": False,
        "problems": problems,
    }
    report["independent_replay"] = "PASS" if not problems else "FAIL"
    if problems:
        report["disposition"] = "FAIL_AUDIT"
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 audit.py RAW.json")
    print(json.dumps(main(Path(sys.argv[1])), indent=2, sort_keys=True))

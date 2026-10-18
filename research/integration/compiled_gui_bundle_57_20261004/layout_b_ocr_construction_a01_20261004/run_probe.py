#!/usr/bin/env python3
"""Read-only OCR probe over retained layout-B engineering screenshots."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / ".git").exists())
SOURCE = REPO / "research/live_control/results/integrated-efficiency-live-orchestration-probe-02"
DETAILS = SOURCE / "arms/ephemeral/task-details.json"
RUNTIME = SOURCE / "arms/ephemeral/runtime"
GEOMETRY = "280x26+499+546"
SCALE = "800%"
PSM = "7"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def task_record(rows: list[dict], task_id: str) -> dict:
    found = [row for row in rows if row["trace"]["task_id"] == task_id]
    if len(found) != 1 or len(found[0]["submission_records"]) != 1:
        raise RuntimeError(f"expected one task and exact scorer record: {task_id}")
    return found[0]


def main() -> None:
    details = json.loads(DETAILS.read_text())
    task5, task6 = task_record(details, "task-5"), task_record(details, "task-6")
    tokens = {
        task["trace"]["task_id"]: task["submission_records"][0]["expected_token"]
        for task in (task5, task6)
    }
    pngs = sorted(RUNTIME.glob("*.png"), key=lambda path: int(path.stem))
    buckets = {
        "task-5": [p for p in pngs if 93 <= int(p.stem) < 115],
        "task-6": [p for p in pngs if int(p.stem) >= 115],
    }
    negative = RUNTIME / "068.png"
    rows: list[dict] = []
    command_template = "magick INPUT -crop 280x26+499+546 +repage -resize 800% CROP; tesseract CROP stdout -l eng --psm 7"
    with tempfile.TemporaryDirectory(prefix="layoutb-ocr-a01-", dir=REPO / "work") as tmp:
        tmpdir = Path(tmp)
        for task_id, frames in [("task-4-empty-negative", [negative]), *buckets.items()]:
            expected = None if task_id.startswith("task-4") else tokens[task_id]
            for frame in frames:
                crop = tmpdir / f"{frame.stem}.png"
                magick_cmd = ["magick", str(frame), "-crop", GEOMETRY, "+repage", "-resize", SCALE, str(crop)]
                magick_run = subprocess.run(magick_cmd, capture_output=True, text=True)
                tess_cmd = ["tesseract", str(crop), "stdout", "-l", "eng", "--psm", PSM]
                if magick_run.returncode == 0:
                    tess_run = subprocess.run(tess_cmd, capture_output=True, text=True)
                    raw = tess_run.stdout
                    tess_rc = tess_run.returncode
                    crop_digest = sha256(crop)
                else:
                    raw = ""
                    tess_rc = None
                    crop_digest = None
                normalized = raw.strip()
                rows.append({
                    "task_id": task_id,
                    "frame": frame.relative_to(REPO).as_posix(),
                    "frame_number": int(frame.stem),
                    "frame_sha256": sha256(frame),
                    "crop_geometry": GEOMETRY,
                    "crop_resize": SCALE,
                    "crop_sha256": crop_digest,
                    "command": command_template.replace("INPUT", str(frame)).replace("CROP", str(crop)),
                    "magick_exit": magick_run.returncode,
                    "tesseract_exit": tess_rc,
                    "raw_stdout": raw,
                    "stripped_output": normalized,
                    "expected_token": expected,
                    "exact_match": normalized == expected if expected is not None else False,
                })
    result = {
        "schema": "layout_b_ocr_construction_a01_raw_v1",
        "classification": "retrospective construction diagnostic; not formal/live comparison",
        "source_run_report_sha256": sha256(SOURCE / "report.json"),
        "source_task_details_sha256": sha256(DETAILS),
        "tesseract_version": subprocess.run(["tesseract", "--version"], capture_output=True, text=True).stdout.splitlines()[0],
        "magick_version": subprocess.run(["magick", "-version"], capture_output=True, text=True).stdout.splitlines()[0],
        "method": {"geometry": GEOMETRY, "resize": SCALE, "language": "eng", "psm": PSM, "normalization": "strip outer whitespace only"},
        "frame_count": len(rows),
        "rows": rows,
    }
    (PACKAGE / "RAW.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

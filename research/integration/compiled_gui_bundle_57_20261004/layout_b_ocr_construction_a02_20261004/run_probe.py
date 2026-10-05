#!/usr/bin/env python3
"""Frozen, read-only OCR construction probe on untouched plain/persistent arms."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path, PurePosixPath

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / ".git").exists())
SOURCE = REPO / "research/live_control/results/integrated-efficiency-live-orchestration-probe-02"
RUNTIME = SOURCE / "arms"
REPORT = SOURCE / "report.json"
GEOMETRY = "280x26+499+546"
RESIZE = "800%"
PSM = "7"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(command: list[str], *, binary: bool = False):
    return subprocess.run(command, capture_output=True, text=not binary)


def pngs_for_arm(arm: str) -> list[Path]:
    return sorted((RUNTIME / arm / "runtime").glob("*.png"), key=lambda p: int(p.stem))


def source_number(task: dict) -> int:
    image_name = PurePosixPath(task["source"]["image"].replace("\\", "/")).name
    return int(Path(image_name).stem)


def get_task(details: list[dict], task_id: str) -> dict:
    matches = [item for item in details if item["trace"]["task_id"] == task_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {task_id}, found {len(matches)}")
    task = matches[0]
    if task["trace"]["layout"] != "B" or len(task["submission_records"]) != 1:
        raise RuntimeError(f"layout or scorer record mismatch: {task_id}")
    scorer = task["submission_records"][0]
    if scorer["exact"] is not True or scorer["submitted_values"] != [scorer["expected_token"]]:
        raise RuntimeError(f"expected an exact independent submission: {task_id}")
    return task


def ocr_one(image: Path, tmp: Path) -> dict:
    crop = tmp / f"{image.parent.parent.name}-{image.stem}.png"
    magick_cmd = [
        "magick", str(image), "-crop", GEOMETRY, "+repage", "-alpha", "remove",
        "-colorspace", "Gray", "-resize", RESIZE, "-bordercolor", "white", "-border", "32", str(crop),
    ]
    magick_run = run(magick_cmd)
    if magick_run.returncode:
        raise RuntimeError(f"ImageMagick failed for {image}: {magick_run.stderr}")
    tess_cmd = ["tesseract", str(crop), "stdout", "-l", "eng", "--psm", PSM]
    tess_run = run(tess_cmd)
    pixels = run(["magick", str(crop), "-colorspace", "Gray", "-depth", "8", "gray:-"], binary=True)
    if pixels.returncode:
        raise RuntimeError(f"pixel digest failed for {crop}: {pixels.stderr!r}")
    return {
        "frame": image.relative_to(REPO).as_posix(),
        "frame_number": int(image.stem),
        "frame_sha256": sha256_file(image),
        "crop_geometry": GEOMETRY,
        "crop_resize": RESIZE,
        "crop_transform": "alpha-remove; colorspace Gray; white border 32 px",
        "crop_pixel_sha256": sha256_bytes(pixels.stdout),
        "command": {"magick": magick_cmd, "tesseract": tess_cmd},
        "magick_exit": magick_run.returncode,
        "tesseract_exit": tess_run.returncode,
        "raw_stdout": tess_run.stdout,
        "stripped_output": tess_run.stdout.strip(),
    }


def main() -> None:
    if not (REPO / "work").is_dir():
        raise RuntimeError("expected existing work/ scratch directory")
    report = json.loads(REPORT.read_text())
    if report.get("claim") != "engineering orchestration only; excluded from formal comparison":
        raise RuntimeError("source run disposition changed")
    details_by_arm = {
        arm: json.loads((RUNTIME / arm / "task-details.json").read_text())
        for arm in ("ephemeral", "plain", "persistent")
    }
    dev_task = get_task(details_by_arm["ephemeral"], "task-4")
    dev_token = dev_task["submission_records"][0]["expected_token"]
    dev_frame_number = 77
    dev_frame = RUNTIME / "ephemeral" / "runtime" / f"{dev_frame_number:03d}.png"
    dev_source_frame = RUNTIME / "ephemeral" / "runtime" / f"{source_number(dev_task):03d}.png"
    task_details_hashes = {arm: sha256_file(RUNTIME / arm / "task-details.json") for arm in details_by_arm}
    start_ns = time.time_ns()
    with tempfile.TemporaryDirectory(prefix="layoutb-a02-", dir=REPO / "work") as temp:
        tmp = Path(temp)
        dev = ocr_one(dev_frame, tmp)
        dev["expected_token"] = dev_token
        dev["exact_match"] = dev["stripped_output"] == dev_token
        dev_source_output = ocr_one(dev_source_frame, tmp)
        dev_source_output["expected_token"] = dev_token
        dev_source_output["exact_match"] = dev_source_output["stripped_output"] == dev_token
        results = []
        for arm in ("plain", "persistent"):
            tasks = [get_task(details_by_arm[arm], f"task-{i}") for i in (4, 5, 6)]
            starts = [source_number(task) for task in tasks]
            images = pngs_for_arm(arm)
            last = max((int(path.stem) for path in images), default=0) + 1
            for i, task in enumerate(tasks):
                begin = starts[i]
                end = starts[i + 1] if i + 1 < len(starts) else last
                frame_paths = [path for path in images if begin <= int(path.stem) < end]
                scorer = task["submission_records"][0]
                for img in frame_paths:
                    frame_result = ocr_one(img, tmp)
                    frame_result.update({
                        "arm": arm,
                        "task_id": task["trace"]["task_id"],
                        "task_start_frame": begin,
                        "task_end_exclusive": end,
                        "expected_token": scorer["expected_token"],
                        "exact_match": frame_result["stripped_output"] == scorer["expected_token"],
                        "is_task_source_frame": int(img.stem) == begin,
                    })
                    results.append(frame_result)
    end_ns = time.time_ns()
    raw = {
        "schema": "layout_b_ocr_construction_a02_raw_v1",
        "experiment_id": "layout_b_ocr_construction_a02_20261004",
        "classification": "held-out construction diagnostic over retained synthetic-grounding screenshots; not formal/live comparison",
        "host": "Darwin ARM64",
        "started_utc": datetime.fromtimestamp(start_ns / 1e9, timezone.utc).isoformat(),
        "started_epoch_ns": start_ns,
        "ended_epoch_ns": end_ns,
        "elapsed_ns": end_ns - start_ns,
        "source_run_report_sha256": sha256_file(REPORT),
        "source_task_details_sha256_by_arm": task_details_hashes,
        "source_run_report_claim": report["claim"],
        "source_model_calls": report["model_calls"],
        "source_synthetic_grounding_invocations": report["synthetic_grounding_invocations"],
        "runner_sha256": sha256_file(Path(__file__)),
        "method": {
            "crop_geometry": GEOMETRY,
            "resize": RESIZE,
            "transform": "alpha-remove; colorspace Gray; white border 32 px",
            "ocr": ["tesseract", "-l", "eng", "--psm", PSM],
            "normalization": "strip outer whitespace only; exact comparison; no fuzzy or character normalization",
        },
        "versions": {
            "tesseract": run(["tesseract", "--version"]).stdout.splitlines()[0],
            "imagemagick": run(["magick", "-version"]).stdout.splitlines()[0],
            "python": run(["python3", "--version"]).stdout.strip() or run(["python3", "--version"]).stderr.strip(),
        },
        "development": {
            "arm": "ephemeral",
            "task_id": "task-4",
            "expected_token": dev_token,
            "entered_value_frame": dev,
            "empty_source_frame": dev_source_output,
        },
        "heldout_frame_count": len(results),
        "heldout_rows": results,
    }
    (PACKAGE / "RAW.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment_id": raw["experiment_id"],
        "heldout_frame_count": raw["heldout_frame_count"],
        "dev_output": dev["stripped_output"],
        "dev_exact": dev["exact_match"],
        "heldout_exact_by_arm_task": {
            f"{arm}/{task}": [r["frame_number"] for r in results if r["arm"] == arm and r["task_id"] == task and r["exact_match"]]
            for arm in ("plain", "persistent") for task in ("task-4", "task-5", "task-6")
        },
        "elapsed_ns": raw["elapsed_ns"],
        "versions": raw["versions"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

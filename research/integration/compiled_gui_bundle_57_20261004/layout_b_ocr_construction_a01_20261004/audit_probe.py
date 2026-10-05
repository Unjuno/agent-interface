#!/usr/bin/env python3
"""Independently re-run and audit the frozen A01 screenshot OCR records."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / ".git").exists())
SOURCE = REPO / "research/live_control/results/integrated-efficiency-live-orchestration-probe-02"
RAW_PATH = PACKAGE / "RAW.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_ocr(frame: Path, tmp: Path) -> tuple[str, int, str]:
    crop = tmp / (frame.stem + ".png")
    magick = subprocess.run(
        ["magick", str(frame), "-crop", "280x26+499+546", "+repage", "-resize", "800%", str(crop)],
        capture_output=True, text=True,
    )
    if magick.returncode:
        raise RuntimeError(magick.stderr)
    proc = subprocess.run(["tesseract", str(crop), "stdout", "-l", "eng", "--psm", "7"], capture_output=True, text=True)
    return proc.stdout, proc.returncode, digest(crop)


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    details_path = SOURCE / "arms/ephemeral/task-details.json"
    report_path = SOURCE / "report.json"
    details = json.loads(details_path.read_text())
    report = json.loads(report_path.read_text())
    assert raw["schema"] == "layout_b_ocr_construction_a01_raw_v1"
    assert raw["classification"] == "retrospective construction diagnostic; not formal/live comparison"
    assert report["claim"] == "engineering orchestration only; excluded from formal comparison"
    assert report["model_calls"] == 0 and report["synthetic_grounding_invocations"] == 14
    assert digest(report_path) == raw["source_run_report_sha256"]
    assert digest(details_path) == raw["source_task_details_sha256"]
    assert raw["method"] == {"geometry": "280x26+499+546", "resize": "800%", "language": "eng", "psm": "7", "normalization": "strip outer whitespace only"}

    submissions = {}
    for row in details:
        tid = row["trace"]["task_id"]
        if tid in ("task-5", "task-6"):
            submissions[tid] = row["submission_records"][0]
    assert {key: val["expected_token"] for key, val in submissions.items()} == {"task-5": "t991028-5", "task-6": "t991028-6"}
    expected_frames = {"task-4-empty-negative": [68]}
    runtime = SOURCE / "arms/ephemeral/runtime"
    for task_id, low, high in (("task-5", 93, 115), ("task-6", 115, 128)):
        expected_frames[task_id] = sorted(int(p.stem) for p in runtime.glob("*.png") if low <= int(p.stem) < high)

    rows = raw["rows"]
    assert raw["frame_count"] == len(rows) == sum(map(len, expected_frames.values()))
    grouped = {key: [r for r in rows if r["task_id"] == key] for key in expected_frames}
    assert {key: sorted(r["frame_number"] for r in group) for key, group in grouped.items()} == expected_frames
    source_mismatches = []
    ocr_replay_mismatches = []
    crop_byte_hash_mismatches = []
    with tempfile.TemporaryDirectory(prefix="layoutb-a01-audit-", dir=REPO / "work") as td:
        tmp = Path(td)
        for task_id, group in grouped.items():
            for row in group:
                frame = REPO / row["frame"]
                if digest(frame) != row["frame_sha256"]:
                    source_mismatches.append(row["frame"])
                    continue
                observed, rc, crop_hash = run_ocr(frame, tmp)
                if observed != row["raw_stdout"] or rc != row["tesseract_exit"]:
                    ocr_replay_mismatches.append(row["frame"])
                if crop_hash != row["crop_sha256"]:
                    crop_byte_hash_mismatches.append(row["frame"])
                expected = submissions[task_id]["expected_token"] if task_id in submissions else None
                if expected != row["expected_token"] or row["exact_match"] != (row["stripped_output"] == expected if expected else False):
                    ocr_replay_mismatches.append(row["frame"])
    exact_by_task = {key: [r["frame_number"] for r in group if r["exact_match"]] for key, group in grouped.items()}
    source_outputs = {key: grouped[key][0]["stripped_output"] for key in ("task-5", "task-6")}
    found = {"empty_source": grouped["task-4-empty-negative"][0]["stripped_output"], "heldout_source_outputs": source_outputs, "exact_frames": exact_by_task}
    exactness_success = all(exact_by_task[k] for k in ("task-5", "task-6")) and all(not v for v in source_outputs.values())
    replay_success = not source_mismatches and not ocr_replay_mismatches
    execution_recipe_aligned = raw["method"].get("transform") == "alpha-remove; colorspace Gray; white border 32 px"
    # The development exploration that selected this crop/scale/PSM included
    # grayscale conversion and a 32px white border; A01's frozen runner omitted
    # those transforms. Preserve its measured OCR outputs, but do not call it a
    # valid held-out check of the selected development pipeline.
    success = replay_success and exactness_success and execution_recipe_aligned
    audit = {
        "schema": "layout_b_ocr_construction_a01_audit_v1",
        "status": "PASS_CONSTRUCTION_HELDOUT_TASKS_5_6" if success else ("HOLD_PREPROCESSING_DEVIATION_UNALIGNED_DEVELOPMENT" if not execution_recipe_aligned else "FAIL_FROZEN_LAYOUT_B_OCR_EXACTNESS"),
        "execution_recipe_aligned_with_development": execution_recipe_aligned,
        "replay_status": "PASS_SOURCE_AND_OCR_REPLAY" if replay_success else "FAIL_SOURCE_OR_OCR_REPLAY",
        "raw_sha256": digest(RAW_PATH),
        "runner_sha256": digest(PACKAGE / "run_probe.py"),
        "auditor_sha256": digest(Path(__file__)),
        "source_hash_mismatches": source_mismatches,
        "ocr_replay_mismatches": ocr_replay_mismatches,
        "derived_crop_byte_hash_mismatches": crop_byte_hash_mismatches,
        "derived_crop_pixel_content": "not retained in the original run; its byte hash changes on regeneration, so only the saved OCR output and source-image hash are independently replayed",
        "frame_count": len(rows),
        "exact_frames_by_task": exact_by_task,
        "source_outputs_by_task": source_outputs,
        "negative_empty_source_output": found["empty_source"],
        "meets_frozen_decision": success,
        "scope": "reproduction and exact OCR-readout check on retained synthetic-grounding engineering screenshots only; no live execution or efficiency result",
    }
    (PACKAGE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

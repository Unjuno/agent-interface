#!/usr/bin/env python3
"""Independent replay and decision audit for the A02 OCR construction probe."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / ".git").exists())
SOURCE = REPO / "research/live_control/results/integrated-efficiency-live-orchestration-probe-02"
ARMS = SOURCE / "arms"
RAW_PATH = PACKAGE / "RAW.json"


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def pixel_sha(crop: Path) -> str:
    result = subprocess.run(["magick", str(crop), "-colorspace", "Gray", "-depth", "8", "gray:-"], capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace"))
    return hashlib.sha256(result.stdout).hexdigest()


def replay(image: Path, tmp: Path) -> tuple[str, int, str]:
    crop = tmp / f"audit-{image.parent.parent.name}-{image.stem}.png"
    transformed = subprocess.run([
        "magick", str(image), "-crop", "280x26+499+546", "+repage", "-alpha", "remove",
        "-colorspace", "Gray", "-resize", "800%", "-bordercolor", "white", "-border", "32", str(crop),
    ], capture_output=True, text=True)
    if transformed.returncode:
        raise RuntimeError(transformed.stderr)
    ocr = subprocess.run(["tesseract", str(crop), "stdout", "-l", "eng", "--psm", "7"], capture_output=True, text=True)
    return ocr.stdout, ocr.returncode, pixel_sha(crop)


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    report_path = SOURCE / "report.json"
    report = json.loads(report_path.read_text())
    assert report["claim"] == "engineering orchestration only; excluded from formal comparison"
    assert report["model_calls"] == 0 and report["synthetic_grounding_invocations"] == 14
    assert raw["schema"] == "layout_b_ocr_construction_a02_raw_v1"
    assert raw["source_run_report_sha256"] == file_sha(report_path)
    assert raw["source_run_report_claim"] == report["claim"]
    assert raw["source_model_calls"] == 0 and raw["source_synthetic_grounding_invocations"] == 14
    assert raw["method"] == {
        "crop_geometry": "280x26+499+546",
        "resize": "800%",
        "transform": "alpha-remove; colorspace Gray; white border 32 px",
        "ocr": ["tesseract", "-l", "eng", "--psm", "7"],
        "normalization": "strip outer whitespace only; exact comparison; no fuzzy or character normalization",
    }
    details = {arm: json.loads((ARMS / arm / "task-details.json").read_text()) for arm in ("ephemeral", "plain", "persistent")}
    if raw["source_task_details_sha256_by_arm"] != {arm: file_sha(ARMS / arm / "task-details.json") for arm in details}:
        raise AssertionError("task-details source hash mismatch")
    submissions = {}
    sources = {}
    for arm in ("plain", "persistent"):
        for task in details[arm]:
            tid = task["trace"]["task_id"]
            if tid not in ("task-4", "task-5", "task-6"):
                continue
            assert task["trace"]["layout"] == "B"
            assert len(task["submission_records"]) == 1
            scorer = task["submission_records"][0]
            assert scorer["exact"] is True and scorer["submitted_values"] == [scorer["expected_token"]]
            submissions[(arm, tid)] = scorer["expected_token"]
            sources[(arm, tid)] = int(Path(PurePosixPath(task["source"]["image"].replace("\\", "/")).name).stem)
    assert len(submissions) == 6

    by_case = {}
    for row in raw["heldout_rows"]:
        key = (row["arm"], row["task_id"])
        by_case.setdefault(key, []).append(row)
    assert set(by_case) == set(submissions)
    source_hash_mismatches = []
    replay_mismatches = []
    pixel_digest_mismatches = []
    oracle_mismatches = []
    with tempfile.TemporaryDirectory(prefix="layoutb-a02-audit-", dir=REPO / "work") as td:
        tmp = Path(td)
        for key, rows in by_case.items():
            rows.sort(key=lambda row: row["frame_number"])
            arm, task_id = key
            assert rows[0]["frame_number"] == sources[key]
            for row in rows:
                frame = REPO / row["frame"]
                if file_sha(frame) != row["frame_sha256"]:
                    source_hash_mismatches.append(row["frame"])
                    continue
                stdout, exit_code, pixels = replay(frame, tmp)
                if stdout != row["raw_stdout"] or exit_code != row["tesseract_exit"]:
                    replay_mismatches.append(row["frame"])
                if pixels != row["crop_pixel_sha256"]:
                    pixel_digest_mismatches.append(row["frame"])
                expected = submissions[key]
                if row["expected_token"] != expected or row["exact_match"] != (row["stripped_output"] == expected):
                    oracle_mismatches.append(row["frame"])

    exact_frames = {
        f"{arm}/{task}": [row["frame_number"] for row in rows if row["exact_match"]]
        for (arm, task), rows in sorted(by_case.items())
    }
    source_negative = {
        f"{arm}/{task}": {
            "frame": rows[0]["frame_number"],
            "ocr": rows[0]["stripped_output"],
            "exact_match": rows[0]["exact_match"],
        }
        for (arm, task), rows in sorted(by_case.items())
    }
    positive_cases = all(exact_frames.values())
    negative_cases = all(not row["exact_match"] for row in source_negative.values())
    replay_pass = not source_hash_mismatches and not replay_mismatches and not pixel_digest_mismatches and not oracle_mismatches
    method_pass = raw["development"]["entered_value_frame"]["exact_match"] is True and raw["development"]["empty_source_frame"]["exact_match"] is False
    criterion_pass = positive_cases and negative_cases and method_pass
    status = "PASS_CONSTRUCTION_HELDOUT_6_OF_6" if replay_pass and criterion_pass else "FAIL_FROZEN_LAYOUT_B_OCR_EXACTNESS"
    audit = {
        "schema": "layout_b_ocr_construction_a02_audit_v1",
        "status": status,
        "replay_status": "PASS_SOURCE_CROP_PIXEL_AND_OCR_REPLAY" if replay_pass else "FAIL_RAW_SOURCE_OR_REPLAY_INTEGRITY",
        "raw_sha256": file_sha(RAW_PATH),
        "runner_sha256": file_sha(PACKAGE / "run_probe.py"),
        "auditor_sha256": file_sha(Path(__file__)),
        "source_hash_mismatches": source_hash_mismatches,
        "ocr_replay_mismatches": replay_mismatches,
        "crop_pixel_digest_mismatches": pixel_digest_mismatches,
        "oracle_mismatches": oracle_mismatches,
        "heldout_frame_count": len(raw["heldout_rows"]),
        "exact_frame_numbers_by_arm_task": exact_frames,
        "empty_source_frame_by_arm_task": source_negative,
        "development_exact_positive": raw["development"]["entered_value_frame"]["exact_match"] is True,
        "development_empty_negative": raw["development"]["empty_source_frame"]["exact_match"] is False,
        "meets_frozen_decision": replay_pass and criterion_pass,
        "visual_confirmation": "not assessed by this data-replay auditor; see VISUAL_REVIEW.md for author inspection",
        "scope": "held-out construction OCR readout on saved synthetic-grounding screenshots only; no GUI input or efficiency result",
    }
    (PACKAGE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

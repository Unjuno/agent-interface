from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageStat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FREEZE = json.loads((HERE.parent / "FREEZE.json").read_text(encoding="utf-8"))
INPUTS = json.loads((HERE / "INPUTS.json").read_text(encoding="utf-8"))
RESULT = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
REVIEW = json.loads((HERE / "VISUAL_REVIEW.json").read_text(encoding="utf-8"))


def git_blob(commit: str, path: str) -> str:
    return subprocess.run(["git", "rev-parse", f"{commit}:{path}"], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout.strip()


def blob_bytes(oid: str) -> bytes:
    return subprocess.run(["git", "cat-file", "blob", oid], cwd=ROOT,
                          check=True, capture_output=True).stdout

assert FREEZE["source_commit"] == INPUTS["source_main_snapshot"]
for path, record in FREEZE["sources"].items():
    assert git_blob(FREEZE["source_commit"], path) == record["git_blob"], path
    assert git_blob(INPUTS["source_main_tip_checked"], path) == record["git_blob"], path

source_review = INPUTS["source_visual_review"]
assert git_blob(INPUTS["source_pr_head"], source_review["path"]) == source_review["git_blob"]
assert hashlib.sha256(blob_bytes(source_review["git_blob"])).hexdigest() == source_review["sha256"]

expected = []
for case in INPUTS["tasks"]:
    png_path = HERE / case["image_file"]
    image_data = png_path.read_bytes()
    assert hashlib.sha256(image_data).hexdigest() == case["image_sha256"], case["task"]
    assert hashlib.sha256(blob_bytes(case["image_git_blob"])).hexdigest() == case["image_sha256"]
    answer_data = blob_bytes(case["answer_git_blob"])
    assert hashlib.sha256(answer_data).hexdigest() == case["answer_sha256"]
    answer = json.loads(answer_data)
    assert answer["field_point"] == case["field_point"]
    assert answer["submit_point"] == case["submit_point"]
    with Image.open(png_path) as source:
        image = source.convert("RGB")
    assert image.size == (1280, 800)
    for role in ("field", "submit"):
        x, y = case[f"{role}_point"]
        patch = image.crop((x - 12, y - 12, x + 12, y + 12))
        max_stddev = max(ImageStat.Stat(patch).stddev)
        status = "FLAT_REFUSED" if max_stddev < 8 else "VALID"
        expected.append((case["task"], role, status, status == "VALID", round(max_stddev, 6)))

actual = [
    (row["task"], row["role"], row["status"], row["eligible"], row["max_patch_stddev"])
    for row in RESULT["cases"]
]
assert actual == expected, {"actual": actual, "expected": expected}
assert RESULT["summary"] == {
    "coordinate_count": 10, "valid": 7, "flat_refused": 3,
    "other_status": 0, "input_dispatch_count": 0,
    "model_call_count": 0, "gui_call_count": 0,
}
assert len(REVIEW["screenshots"]) == 5
assert "post-hoc" in REVIEW["adjudication"]
assert all("visible at proposed point" in item["field"] and
           "visible at proposed point" in item["save"] for item in REVIEW["screenshots"])

failure = (HERE / "out/PREREGISTERED_EXPECTATION_FAILURE.txt").read_text(encoding="utf-8", errors="replace")
assert "Ran 2 tests" in failure and "FAILED (failures=2)" in failure
assert "'status': 'VALID'" in failure
assert "(4, 'field', {'status': 'FLAT_REFUSED'" in failure

print(json.dumps({
    "status": "PASS_A02_SOURCE_AND_OUTCOME_AUDIT",
    "frozen_runtime_sources": len(FREEZE["sources"]),
    "pinned_screenshots": len(INPUTS["tasks"]),
    "coordinate_count": len(expected),
    "valid": 7,
    "flat_refused": 3,
    "hypothesis_test_exit": 1,
    "input_dispatch_count": 0,
    "interpretation": "offline descriptive result; no semantic or task-effect claim",
}, sort_keys=True))

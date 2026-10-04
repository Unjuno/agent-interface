"""Classify the retained C-arm safe-yields without replaying the study."""
import hashlib
import json
import subprocess
from pathlib import Path

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
REF = "58bcbb4c45501880db8782158ddd3add3b765984"
BASE = "research/integration/compiled_comparison_57_4d74_20261004/a05"


def show(path):
    return subprocess.check_output(["git", "-C", REPO, "show", f"{REF}:{path}"])


adapter_path = f"{BASE}/compiled_adapter.py"
adapter = show(adapter_path)
adapter_text = adapter.decode("utf-8")
assert "boxes={'A':(120,394,332,409),'B':(499,544,799,573)}" in adapter_text
assert "self.task['token']==ocr.stdout.strip()" in adapter_text

failures = []
for block, task_num in ((1, 5), (1, 6), (2, 6)):
    path = f"{BASE}/formal-output/block-{block}/C/task-{task_num}.json"
    row = json.loads(show(path))
    caller = row["caller"]
    receipt = row["graph"]["receipt"]
    expected = row["task"]["token"]
    filled = [o for o in row["graph"]["raw_observations"] if o["state"] == "filled"]
    assert caller["outcome"] == "EXECUTION_INCOMPLETE"
    assert caller["reason"] == "effect_failed"
    assert receipt["outcome"] == "SAFE_YIELD"
    assert receipt["reason"] == "effect_failed"
    assert receipt["pending_effect"]["action"] == "enter"
    assert receipt["pending_effect"]["expected_effect"] == {"exact_token_visible": True}
    assert len(receipt["transitions"]) == 1
    assert receipt["transitions"][0]["action"] == "enter"
    assert len(filled) == 1
    observation = filled[0]
    recognized = observation["ocr"]["stdout"].strip()
    assert expected.startswith("t") and recognized == expected[1:]
    assert observation["normalized"]["predicates"]["exact_token_visible"] is False
    enter = next(p for p in row["programs"] if p["label"] == "compiled-enter")
    assert enter["terminal"]["status"] == "completed"
    assert enter["terminal"]["release"]["verified"] is True
    assert not any(p["label"] == "compiled-submit" for p in row["programs"])
    failures.append({
        "block": block,
        "task": task_num,
        "task_id": row["task"]["task_id"],
        "expected_token": expected,
        "ocr_stdout": observation["ocr"]["stdout"],
        "failed_effect": "exact_token_visible",
        "completed_action": "enter",
        "enter_release_verified": True,
        "submit_program_present": False,
        "observation_sequence": observation["normalized"]["sequence"],
        "evidence_ref": observation["normalized"]["evidence_ref"],
        "image_sha256": observation["image_sha256"],
    })

assert len(failures) == 3
visual_review = [
    {
        "block": item["block"],
        "task": item["task"],
        "evidence_ref": item["evidence_ref"],
        "image_sha256": item["image_sha256"],
        "review_result": "full_expected_token_visible_in_input_field",
        "review_method": "manual visual inspection of the exact archived PNG",
    }
    for item in failures
]
crop_boundary_probe = {
    "frozen_layout_b_box_xyxy": [499, 544, 799, 573],
    "candidate_padded_box_xyxy": [493, 542, 805, 579],
    "candidate_box_status": "visual crop preview only; OCR was not rerun",
    "previews": [
        {
            "block": item["block"],
            "task": item["task"],
            "image_sha256": item["image_sha256"],
            "frozen_crop": "left edge visibly cuts the leading t glyph",
            "candidate_crop": "contains the complete token within the field border",
        }
        for item in failures
    ],
}
report = {
    "source_revision": REF,
    "adapter_source": adapter_path,
    "adapter_sha256": hashlib.sha256(adapter).hexdigest(),
    "scope": "Read-only classification of the three archived A05 C-arm EXECUTION_INCOMPLETE rows; no producer, model, GUI, or study runner executed.",
    "failures": failures,
    "finding": "All three recorded safe-yields follow a completed, verified-release enter action. Each filled-state OCR result omits exactly the leading 't' from the task token, so the exact-match predicate fails and no submit program runs.",
    "visual_review": visual_review,
    "crop_boundary_probe": crop_boundary_probe,
    "interpretation_limit": "Manual review confirms the full expected token is visible in each exact archived frame, and shows the frozen layout-B crop cuts the leading t at its left edge. A locally padded crop preview contains the full token, but Tesseract was unavailable so OCR success on that candidate is unverified. Preserve the formal 9/12 C-arm outcome; validate a candidate repair in a separate construction run before any prospectively frozen allocation.",
}
out = Path(__file__).with_name("C_FAILURE_DIAGNOSTICS.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(report, indent=2, sort_keys=True))

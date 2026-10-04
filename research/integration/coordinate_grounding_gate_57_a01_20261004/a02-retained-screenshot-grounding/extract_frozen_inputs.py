from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REF = "e8f7c02cb98d849312a4889fa4d52ec424088732"
INPUT_BASE = "research/integration/planner_contract_56_4d74_20261004/r02/formal-output/block-2/C/client/runtime/"
A14_BASE = "research/integration/compiled_gui_bundle_57_20261004/a14-lifecycle-cross-task-construction/"
TASKS = [(2, "029.png"), (3, "054.png"), (4, "079.png"), (5, "105.png"), (6, "134.png")]


def blob(path: str) -> tuple[str, bytes]:
    oid = subprocess.run(["git", "rev-parse", f"{REF}:{path}"], cwd=ROOT,
                         check=True, capture_output=True, text=True).stdout.strip()
    data = subprocess.run(["git", "cat-file", "blob", oid], cwd=ROOT,
                          check=True, capture_output=True).stdout
    return oid, data


records = []
for task, filename in TASKS:
    image_path = INPUT_BASE + filename
    answer_path = f"{A14_BASE}task-{task}/answer.json"
    image_oid, image_data = blob(image_path)
    answer_oid, answer_data = blob(answer_path)
    answer = json.loads(answer_data)
    records.append({
        "task": task,
        "image_file": f"inputs/{filename}",
        "image_source_path": image_path,
        "image_git_blob": image_oid,
        "image_sha256": hashlib.sha256(image_data).hexdigest(),
        "answer_source_path": answer_path,
        "answer_git_blob": answer_oid,
        "answer_sha256": hashlib.sha256(answer_data).hexdigest(),
        "field_point": answer["field_point"],
        "submit_point": answer["submit_point"],
        "a14_visual_review_claim": "no visible Value field or Save button" if task == 3
                                  else "field and Save button visible",
    })

review_path = A14_BASE + "VISUAL_REVIEW.md"
review_oid, review_data = blob(review_path)
manifest = {
    "schema": "a02-retained-screenshot-grounding-inputs-v1",
    "source_pr_head": REF,
    "source_main_snapshot": "02953aa83d62e69a787de7732bf172f3f8ef8e1c",
    "source_main_tip_checked": "63980603e4bb6e4b128ed07af3bf7023bc2d4734",
    "source_visual_review": {
        "path": review_path,
        "git_blob": review_oid,
        "sha256": hashlib.sha256(review_data).hexdigest(),
    },
    "tasks": records,
}
for row in records:
    data = blob(row["image_source_path"])[1]
    (HERE / row["image_file"]).write_bytes(data)
(HERE / "INPUTS.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"tasks": len(records), "screenshot_bytes": sum((HERE / r["image_file"]).stat().st_size for r in records), "source_pr_head": REF}, sort_keys=True))

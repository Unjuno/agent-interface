"""Independently re-open raw references and validate composed run records."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from composition import REPO_ROOT, SOURCE_REVISION
from comparison_measurement_v1 import validate_measured_run


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
    if conditions["source_revision"] != SOURCE_REVISION:
        raise SystemExit("source pin mismatch")
    for relative in conditions["source_files"]:
        committed = subprocess.check_output(
            ["git", "show", f"{SOURCE_REVISION}:{relative}"], cwd=ROOT)
        current = (REPO_ROOT / Path(relative)).read_bytes()
        if committed != current:
            raise SystemExit(f"pinned source drift: {relative}")

    audited = []
    for case in ("positive", "missing-usage"):
        case_root = ROOT / "runs" / case
        receipt = json.loads((case_root / "receipt.json").read_text(encoding="utf-8"))
        measured = json.loads((case_root / "measured_run.json").read_text(encoding="utf-8"))
        declared = json.loads((case_root / "summary.json").read_text(encoding="utf-8"))
        actual_refs = set()
        for ref in receipt["raw_refs"]:
            raw_path = case_root / "recorder" / Path(*ref["path"].split("/"))
            digest = sha256(raw_path)
            if digest != ref["sha256"]:
                raise SystemExit(f"raw hash mismatch: {case}/{ref['path']}")
            actual_refs.add((ref["path"], digest))
        if len(actual_refs) != len(receipt["raw_refs"]):
            raise SystemExit(f"duplicate or missing raw reference: {case}")
        summary = validate_measured_run(measured)
        projection = {
            "condition": declared["condition"],
            "usage_status": summary["usage_status"],
            "input_tokens": summary["input_tokens"],
            "output_tokens": summary["output_tokens"],
            "task_success": summary["task_success"],
            "model_attempt_count": summary["model_attempt_count"],
            "raw_ref_count": summary["raw_ref_count"],
        }
        for key, value in projection.items():
            if declared.get(key) != value:
                raise SystemExit(f"stored projection mismatch: {case}/{key}")
        attempt = next(event for event in receipt["events"]
                       if event["kind"] == "model_attempt")
        if attempt["status"] != "timeout":
            raise SystemExit(f"terminal provider status drift: {case}")
        if case == "positive":
            if (summary["usage_status"] != "complete" or
                    summary["input_tokens"] != 18 or
                    summary["output_tokens"] != 3):
                raise SystemExit("positive usage case failed its frozen rule")
        elif (summary["usage_status"] != "incomplete" or
              summary["input_tokens"] is not None or
              summary["output_tokens"] is not None):
            raise SystemExit("missing-usage control failed its frozen rule")
        if summary["task_success"] is not None:
            raise SystemExit("accounting-only fixture claimed a task effect")
        audited.append(projection)

    result = {
        "status": "PASS",
        "source_revision": SOURCE_REVISION,
        "source_files_checked": len(conditions["source_files"]),
        "runs_checked": len(audited),
        "raw_reference_count": sum(row["raw_ref_count"] for row in audited),
        "conditions": audited,
    }
    (ROOT / "audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

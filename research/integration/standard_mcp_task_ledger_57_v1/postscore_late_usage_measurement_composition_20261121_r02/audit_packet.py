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


def verify_manifest() -> int:
    manifest = ROOT / "SHA256SUMS"
    if not manifest.exists():
        raise SystemExit("SHA256SUMS manifest is missing")
    expected = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if len(digest) != 64 or name in expected or Path(name).is_absolute() or ".." in Path(name).parts:
            raise SystemExit(f"invalid manifest entry: {line}")
        expected[name] = digest
    generated = {"audit.json", "audit-final.stdout.log", "audit-final.exit-code.txt"}
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != manifest and path.name not in generated
        and path.name != ".gitattributes"
        and "__pycache__" not in path.relative_to(ROOT).parts
        and path.suffix != ".pyc"
    }
    if set(expected) != actual:
        raise SystemExit(f"manifest file set mismatch: missing={sorted(actual-set(expected))}, extra={sorted(set(expected)-actual)}")
    for name, digest in expected.items():
        if sha256(ROOT / Path(*name.split("/"))) != digest:
            raise SystemExit(f"manifest checksum mismatch: {name}")
    return len(expected)


def main() -> None:
    conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
    if conditions["source_revision"] != SOURCE_REVISION:
        raise SystemExit("source pin mismatch")
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    if "** -text whitespace=cr-at-eol" not in attributes:
        raise SystemExit("raw recorder byte-preservation attribute is missing")
    for relative in conditions["source_files"]:
        committed_blob = subprocess.check_output(
            ["git", "rev-parse", f"{SOURCE_REVISION}:{relative}"],
            cwd=REPO_ROOT, text=True).strip()
        worktree_blob = subprocess.check_output(
            ["git", "hash-object", f"--path={relative}",
             str(REPO_ROOT / Path(relative))],
            cwd=REPO_ROOT, text=True).strip()
        if committed_blob != worktree_blob:
            raise SystemExit(f"pinned source drift: {relative}")

    audited = []
    for case in ("positive", "missing-usage"):
        case_root = ROOT / "runs" / case
        receipt = json.loads((case_root / "receipt.json").read_text(encoding="utf-8"))
        measured = json.loads((case_root / "measured_run.json").read_text(encoding="utf-8"))
        declared = json.loads((case_root / "summary.json").read_text(encoding="utf-8"))
        actual_refs = set()
        retained_bytes = []
        for ref in receipt["raw_refs"]:
            raw_path = case_root / "recorder" / Path(*ref["path"].split("/"))
            raw_bytes = raw_path.read_bytes()
            digest = hashlib.sha256(raw_bytes).hexdigest()
            if digest != ref["sha256"]:
                raise SystemExit(f"raw hash mismatch: {case}/{ref['path']}")
            actual_refs.add((ref["path"], digest))
            retained_bytes.append(raw_bytes)
        if len(actual_refs) != len(receipt["raw_refs"]):
            raise SystemExit(f"duplicate or missing raw reference: {case}")
        summary = validate_measured_run(measured)
        score_events = [event for event in measured["task_ledger"]["events"]
                        if event["kind"] == "task_score"]
        tool_events = [event for event in measured["task_ledger"]["events"]
                       if event["kind"] == "tool_call"]
        if len(score_events) != 1 or score_events[0].get("task_success") is not None:
            raise SystemExit(f"task score is not exactly one UNKNOWN: {case}")
        if tool_events:
            raise SystemExit(f"unexpected tool call event: {case}")
        if measured["measurement"]["effect_attribution"].get("effect_observed_ns") is not None:
            raise SystemExit(f"synthetic fixture claims an effect time: {case}")
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
            usage_rows = [raw for raw in retained_bytes
                          if b"thread/tokenUsage/updated" in raw]
            if len(usage_rows) != 1:
                raise SystemExit("positive case lacks one retained usage protocol row")
            row = json.loads(usage_rows[0].decode("utf-8"))
            if (row.get("direction") != "received" or
                    type(row.get("observed_ns")) is not int or
                    row.get("message", {}).get("method") !=
                    "thread/tokenUsage/updated"):
                raise SystemExit("retained usage protocol identity is malformed")
            token_usage = row["message"]["params"]["tokenUsage"]["last"]
            if (token_usage.get("inputTokens") != 18 or
                    token_usage.get("outputTokens") != 3):
                raise SystemExit("retained usage protocol token values drifted")
            if (summary["usage_status"] != "complete" or
                    summary["input_tokens"] != 18 or
                    summary["output_tokens"] != 3):
                raise SystemExit("positive usage case failed its frozen rule")
        else:
            usage_rows = [raw for raw in retained_bytes
                          if b"thread/tokenUsage/updated" in raw]
            if usage_rows:
                raise SystemExit("control unexpectedly retained a late usage row")
            if (summary["usage_status"] != "incomplete" or
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
        "source_check": "git-clean-normalized-worktree-blob-equals-pinned-blob",
        "runs_checked": len(audited),
        "raw_reference_count": sum(row["raw_ref_count"] for row in audited),
        "manifest_files_verified": verify_manifest(),
        "conditions": audited,
    }
    (ROOT / "audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

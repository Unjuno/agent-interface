"""Audit the retained late-usage/native-owner composition packet."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INTEGRATION_ROOT = ROOT.parent
REPO_ROOT = ROOT.parents[3]
import sys
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))

from comparison_measurement_v1 import validate_measured_run


def manifest_hash(path: Path, relative: str) -> str:
    payload = path.read_bytes()
    if "/recorder/raw/" not in f"/{relative}" or not relative.endswith(".bin"):
        payload = payload.replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def verify_manifest() -> int:
    manifest = ROOT / "SHA256SUMS"
    expected = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in expected:
            raise SystemExit(f"duplicate manifest path: {relative}")
        expected[relative] = digest
    excluded = {"SHA256SUMS", "audit.json", "audit-final.stdout.log",
                "audit-final.exit-code.txt", ".gitattributes"}
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*") if path.is_file()
        and path.name not in excluded
        and "__pycache__" not in path.relative_to(ROOT).parts
        and path.suffix != ".pyc"
    }
    if actual != set(expected):
        raise SystemExit("manifest file-set mismatch")
    for relative, digest in expected.items():
        if manifest_hash(ROOT / Path(*relative.split("/")), relative) != digest:
            raise SystemExit(f"manifest checksum mismatch: {relative}")
    return len(expected)


def main() -> None:
    conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
    revision = conditions["source_revision"]
    for relative in conditions["source_files"]:
        pinned = subprocess.check_output(
            ["git", "rev-parse", f"{revision}:{relative}"],
            cwd=REPO_ROOT, text=True).strip()
        current = subprocess.check_output(
            ["git", "hash-object", f"--path={relative}",
             str(REPO_ROOT / relative)], cwd=REPO_ROOT, text=True).strip()
        if pinned != current:
            raise SystemExit(f"source drift: {relative}")

    audited = []
    for name in ("positive", "missing-usage"):
        root = ROOT / "runs" / name
        receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
        measured = json.loads((root / "measured_run.json").read_text(encoding="utf-8"))
        declared = json.loads((root / "summary.json").read_text(encoding="utf-8"))
        top_refs = {(row["path"], row["sha256"]) for row in receipt["raw_refs"]}
        event_refs = set()
        raw_payloads = []
        for ref in receipt["raw_refs"]:
            path = root / "recorder" / Path(*ref["path"].split("/"))
            payload = path.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            if digest != ref["sha256"]:
                raise SystemExit(f"raw digest mismatch: {name}/{ref['path']}")
            raw_payloads.append(payload)
        for event in receipt["events"]:
            for ref in event.get("raw_refs", []):
                event_refs.add((ref["path"], ref["sha256"]))
        if not event_refs <= top_refs:
            raise SystemExit(f"top-level receipt omits event raw refs: {name}")
        attempts = [event for event in receipt["events"]
                    if event["kind"] == "model_attempt"]
        tools = [event for event in receipt["events"]
                 if event["kind"] == "tool_call"]
        if (len(attempts) != 2 or attempts[0]["status"] != "timeout" or
                attempts[1]["attempt_id"] != "attempt-1" or
                any(event["model_attempt_id"] != "attempt-1" for event in tools)):
            raise SystemExit(f"timed-out generation was associated with an action: {name}")
        usage_rows = [payload for payload in raw_payloads
                      if b"thread/tokenUsage/updated" in payload]
        summary = validate_measured_run(measured)
        if (summary["model_attempt_count"] != 2 or
                summary["task_success"] is not None or
                summary["effect_attribution"]["effect_timing"] != "unknown" or
                measured["task_ledger"]["native_owner_binding"][
                    "release_confirmed"] is not True or
                measured["task_ledger"]["native_owner_binding"][
                    "horizon_verified"] is not True):
            raise SystemExit(f"owner binding or UNKNOWN effect drift: {name}")
        projection = {
            "condition": declared["condition"],
            "usage_status": summary["usage_status"],
            "input_tokens": summary["input_tokens"],
            "output_tokens": summary["output_tokens"],
            "task_success": summary["task_success"],
            "effect_timing": summary["effect_attribution"]["effect_timing"],
            "model_attempt_count": summary["model_attempt_count"],
            "tool_call_count": summary["tool_call_count"],
            "raw_ref_count": summary["raw_ref_count"],
        }
        for key, value in projection.items():
            if declared.get(key) != value:
                raise SystemExit(f"stored summary mismatch: {name}/{key}")
        if name == "positive":
            if len(usage_rows) != 1:
                raise SystemExit("positive run must retain one App Server usage row")
            row = json.loads(usage_rows[0].decode("utf-8"))
            tokens = row["message"]["params"]["tokenUsage"]["last"]
            if tokens != {"inputTokens": 18, "outputTokens": 3}:
                raise SystemExit("positive App Server token counts drifted")
            if (summary["usage_status"] != "complete" or
                    summary["input_tokens"] != 28 or
                    summary["output_tokens"] != 5):
                raise SystemExit("positive accounting rule failed")
        else:
            if usage_rows or summary["usage_status"] != "incomplete" or \
                    summary["input_tokens"] is not None or \
                    summary["output_tokens"] is not None:
                raise SystemExit("missing-usage control failed")
        audited.append(projection)

    result = {
        "status": "PASS",
        "source_revision": revision,
        "source_files_checked": len(conditions["source_files"]),
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

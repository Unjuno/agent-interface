"""Independent read-only-input audit for the #3752 one-shot probe."""
import hashlib
import json
from pathlib import Path
import sys


EXPECTED_SOURCE_GIT_BLOB_SHA1 = "70cc62b450c8b9c8aaa0db49b1e116388368fe4c"
EXPECTED_RUNNER_GIT_BLOB_SHA1 = "02c05b5fad754c08fa7e77d268bd593826dd487b"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data):
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def snapshot(root):
    items = {}
    if not root.exists():
        return items
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_dir():
            items[name] = {"kind": "directory"}
        elif path.is_file():
            data = path.read_bytes()
            items[name] = {"kind": "file", "bytes": len(data), "sha256": sha(data)}
    return items


def main():
    output = Path(sys.argv[1]).resolve()
    source = Path(sys.argv[2]).resolve()
    run = output / "attempt"
    raw_bytes = (output / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    errors = []
    attempt_bytes = (source / "runtime/cli_v1/attempt.py").read_bytes()
    runner_bytes = (source / "research/cli_request_temp_crash_3711_v1/experiment.py").read_bytes()
    if git_blob_sha1(attempt_bytes) != EXPECTED_SOURCE_GIT_BLOB_SHA1:
        errors.append("SOURCE_BLOB_SHA1_MISMATCH")
    if git_blob_sha1(runner_bytes) != EXPECTED_RUNNER_GIT_BLOB_SHA1:
        errors.append("RUNNER_BLOB_SHA1_MISMATCH")
    if raw.get("source_git_blob_sha1") != EXPECTED_SOURCE_GIT_BLOB_SHA1:
        errors.append("RAW_SOURCE_BINDING_MISMATCH")
    if raw.get("runner_sha256") != sha(runner_bytes):
        errors.append("RAW_RUNNER_SHA256_MISMATCH")
    temp_path = run / ".request.json.tmp"
    temp = temp_path.read_bytes() if temp_path.exists() else b""
    if raw.get("temp_sha256") != (sha(temp) if temp else None):
        errors.append("TEMP_SHA256_MISMATCH")
    if raw.get("temp_bytes") != len(temp) or not temp:
        errors.append("TEMP_LENGTH_OR_ABSENCE")
    expected_request = {
        "schema": "agent-interface/cli-attempt-v1",
        "operation": "dispatch",
        "arguments": {"capture_directory": str(run / "images")},
        "note": "Request existence does not establish invocation or completion. "
                "Missing report means unknown outcome; never automatically replay."}
    expected_bytes = json.dumps(expected_request, allow_nan=False).encode("utf-8")
    if not expected_bytes.startswith(temp) or len(temp) >= len(expected_bytes):
        errors.append("TEMP_NOT_STRICT_PREFIX_OF_EXPECTED_REQUEST")
    try:
        rows = [json.loads(item["stdout"]) for item in raw["status_rows"]]
    except Exception:
        rows = []
        errors.append("STATUS_STDOUT_INVALID")
    if len(rows) != 2 or any(
            row.get("status") != "unknown_or_incomplete"
            or row.get("replay_allowed") is not False
            or row.get("temporary_files") != [".request.json.tmp"]
            for row in rows):
        errors.append("STATUS_CONTRACT_MISMATCH")
    if any(row.get("exit_code") != 2 for row in raw.get("status_rows", [])):
        errors.append("STATUS_EXIT_CODE_MISMATCH")
    actual = snapshot(run)
    if actual != raw.get("snapshot_before"):
        errors.append("FINAL_SNAPSHOT_DIFFERS_FROM_RAW_PRE_INSPECTION")
    if any(row != raw.get("snapshot_before") for row in raw.get("snapshot_after_each_status", [])):
        errors.append("STATUS_INSPECTION_MUTATED_SNAPSHOT")
    if raw.get("snapshot_after_reuse") != raw.get("snapshot_before"):
        errors.append("REUSE_MUTATED_SNAPSHOT")
    if raw.get("child_exit_code") != 29 or raw.get("backend_marker_exists"):
        errors.append("CRASH_BOUNDARY_OR_BACKEND_MARKER_MISMATCH")
    if (run / "request.json").exists() or (run / "report.json").exists():
        errors.append("FINAL_RECORD_EXISTS")
    if raw.get("retry_called") or raw.get("retry_result", {}).get("error") != "REQUEST_PERSISTENCE_FAILED":
        errors.append("REUSE_NOT_REFUSED_BEFORE_BACKEND")
    if raw.get("errors") != [] or raw.get("disposition") != "PASS_REQUEST_TEMP_CRASH_VISIBLE_NO_REPLAY":
        errors.append("RUNNER_DID_NOT_REPORT_PASS")
    audit = {
        "schema": "agent-interface/issue3752-request-temp-crash-audit-v1",
        "allocation": "issue3752-request-temp-crash-01",
        "raw_sha256": sha(raw_bytes),
        "source_git_blob_sha1": git_blob_sha1(attempt_bytes),
        "runner_git_blob_sha1": git_blob_sha1(runner_bytes),
        "temp_bytes": len(temp),
        "temp_sha256": sha(temp) if temp else None,
        "status_count": len(rows),
        "disposition": "PASS_REQUEST_TEMP_CRASH_AUDITED" if not errors else "FAIL_AUDIT",
        "errors": errors}
    (output / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Independent read-only-input artifact auditor for Issue #3752 successor 02."""
import hashlib
import json
from pathlib import Path
import sys

ATTEMPT_BLOB = "70cc62b450c8b9c8aaa0db49b1e116388368fe4c"
CLI_BLOB = "8a9178b7b8721b8a5471fabcfbeb1cb55976980c"


def sha(b): return hashlib.sha256(b).hexdigest()


def blob(b): return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def snapshot(root):
    result = {}
    if root.exists():
        for p in sorted(root.rglob("*")):
            name = p.relative_to(root).as_posix()
            result[name] = ({"kind": "directory"} if p.is_dir() else
                            {"kind": "file", "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())})
    return result


def main():
    evidence, source = map(lambda x: Path(x).resolve(), sys.argv[1:3])
    raw_bytes = (evidence / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    attempt = (source / "runtime/cli_v1/attempt.py").read_bytes()
    cli = (source / "runtime/cli_v1/__main__.py").read_bytes()
    errors = []
    if blob(attempt) != ATTEMPT_BLOB or raw.get("attempt_blob") != ATTEMPT_BLOB: errors.append("ATTEMPT_BLOB_MISMATCH")
    if blob(cli) != CLI_BLOB or raw.get("cli_blob") != CLI_BLOB: errors.append("CLI_BLOB_MISMATCH")
    if raw.get("attempt_sha256") != sha(attempt) or raw.get("cli_sha256") != sha(cli): errors.append("SOURCE_SHA256_MISMATCH")
    runner = source / "research/integration/issue_3752_request_temp_crash_v2/experiment.py"
    if raw.get("runner_sha256") != sha(runner.read_bytes()): errors.append("RUNNER_SHA256_MISMATCH")
    run = evidence / "attempt"
    actual = snapshot(run)
    if actual != raw.get("snapshot_before") or actual != raw.get("snapshot_after_reuse"): errors.append("FINAL_SNAPSHOT_MISMATCH")
    if raw.get("snapshot_after_status") != [raw.get("snapshot_before"), raw.get("snapshot_before")]: errors.append("STATUS_SNAPSHOT_MISMATCH")
    temp = (run / ".request.json.tmp").read_bytes() if (run / ".request.json.tmp").is_file() else b""
    expected = {"schema":"agent-interface/cli-attempt-v1", "operation":"dispatch",
                "arguments":{"capture_directory":str(run / "images")},
                "note":"Request existence does not establish invocation or completion. Missing report means unknown outcome; never automatically replay."}
    expected_bytes = json.dumps(expected, allow_nan=False).encode()
    if not temp or not expected_bytes.startswith(temp) or len(temp) >= len(expected_bytes): errors.append("TEMP_PREFIX_MISMATCH")
    if raw.get("temp_bytes") != len(temp) or raw.get("temp_sha256") != sha(temp): errors.append("TEMP_HASH_MISMATCH")
    if any((run / name).exists() for name in ("request.json", "report.json")): errors.append("FINAL_RECORD_PRESENT")
    if (evidence / "backend-called").exists() or raw.get("marker_exists") is not False: errors.append("BACKEND_MARKER_PRESENT")
    try: statuses = [json.loads(s["stdout"]) for s in raw["statuses"]]
    except Exception: statuses = []; errors.append("STATUS_JSON_INVALID")
    if len(statuses) != 2 or any(x.get("status") != "unknown_or_incomplete" or x.get("replay_allowed") is not False or x.get("temporary_files") != [".request.json.tmp"] for x in statuses): errors.append("STATUS_CONTRACT_MISMATCH")
    if any(s.get("exit_code") != 2 for s in raw.get("statuses", [])): errors.append("STATUS_EXIT_MISMATCH")
    if raw.get("child_exit") != 29: errors.append("CHILD_EXIT_MISMATCH")
    try: reuse = json.loads(raw["reuse_stdout"])
    except Exception: reuse = {}; errors.append("REUSE_JSON_INVALID")
    if raw.get("reuse_exit") != 2 or reuse.get("error") != "REQUEST_PERSISTENCE_FAILED" or reuse.get("operation_invoked") is not False: errors.append("REUSE_CONTRACT_MISMATCH")
    if raw.get("errors") != [] or raw.get("disposition") != "PASS_SCOPED_REQUEST_TEMP_UNKNOWN_NO_REPLAY": errors.append("RUNNER_NOT_PASS")
    audit = {"schema":"agent-interface/issue3752-request-temp-crash-audit-v2", "allocation":"issue3752-request-temp-crash-successor-02",
             "raw_sha256":sha(raw_bytes), "actual_snapshot":actual, "attempt_blob":blob(attempt), "cli_blob":blob(cli),
             "runner_sha256":sha(runner.read_bytes()), "errors":errors,
             "disposition":"PASS_AUDIT_V2" if not errors else "FAIL_AUDIT_V2"}
    (evidence / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"disposition":audit["disposition"], "errors":errors}, sort_keys=True))
    if errors: raise SystemExit(1)


if __name__ == "__main__": main()

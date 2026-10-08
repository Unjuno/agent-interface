"""Independent artifact audit: evidence is input-only, result is separate output."""
import hashlib
import json
from pathlib import Path
import sys

ATTEMPT_BLOB = "70cc62b450c8b9c8aaa0db49b1e116388368fe4c"
CLI_BLOB = "8a9178b7b8721b8a5471fabcfbeb1cb55976980c"
RUNNER_SHA256 = "81092a01f39ce8da04ce163119e032ca68e8634dff2909c2d12e7c70330af0a9"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def snapshot(root):
    values = {}
    if root.exists():
        for path in sorted(root.rglob("*")):
            name = path.relative_to(root).as_posix()
            values[name] = ({"kind": "directory"} if path.is_dir() else
                            {"kind": "file", "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())})
    return values


def main():
    evidence, source, output = [Path(arg).resolve() for arg in sys.argv[1:4]]
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("STOP_AUDIT_OUTPUT_NOT_EMPTY")
    raw_path = evidence / "raw.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    run = evidence / "attempt"
    attempt_bytes = (source / "runtime/cli_v1/attempt.py").read_bytes()
    cli_bytes = (source / "runtime/cli_v1/__main__.py").read_bytes()
    runner_bytes = (source / "research/integration/issue_3752_request_temp_crash_v2/experiment.py").read_bytes()
    errors = []
    if sha(raw_bytes) != "6d0cc630d979b19263450f8220ac0bce184e0ebdc5ea267ab76f67d1e994ea68": errors.append("RAW_HASH_MISMATCH")
    if blob(attempt_bytes) != ATTEMPT_BLOB or raw.get("attempt_blob") != ATTEMPT_BLOB: errors.append("ATTEMPT_BLOB_MISMATCH")
    if blob(cli_bytes) != CLI_BLOB or raw.get("cli_blob") != CLI_BLOB: errors.append("CLI_BLOB_MISMATCH")
    if sha(runner_bytes) != RUNNER_SHA256 or raw.get("runner_sha256") != RUNNER_SHA256: errors.append("RUNNER_HASH_MISMATCH")
    actual = snapshot(run)
    if actual != raw.get("snapshot_before"): errors.append("ACTUAL_PRE_REUSE_SNAPSHOT_MISMATCH")
    if raw.get("snapshot_after_status") != [actual, actual] or raw.get("snapshot_after_reuse") != actual: errors.append("SNAPSHOT_SEQUENCE_MISMATCH")
    temp = run / ".request.json.tmp"
    temp_bytes = temp.read_bytes() if temp.is_file() else b""
    expected = {"schema":"agent-interface/cli-attempt-v1", "operation":"dispatch",
                "arguments":{"capture_directory":"/out/attempt/images"},
                "note":"Request existence does not establish invocation or completion. Missing report means unknown outcome; never automatically replay."}
    expected_bytes = json.dumps(expected, allow_nan=False).encode()
    if not temp_bytes or not expected_bytes.startswith(temp_bytes) or len(temp_bytes) >= len(expected_bytes): errors.append("TEMP_NOT_EXPECTED_STRICT_PREFIX")
    if raw.get("temp_bytes") != len(temp_bytes) or raw.get("temp_sha256") != sha(temp_bytes): errors.append("TEMP_HASH_OR_LENGTH_MISMATCH")
    if any((run / name).exists() for name in ("request.json", "report.json")): errors.append("FINAL_RECORD_PRESENT")
    try:
        statuses = [json.loads(item["stdout"]) for item in raw["statuses"]]
    except Exception:
        statuses = []
        errors.append("STATUS_JSON_INVALID")
    if len(statuses) != 2 or any(item.get("status") != "unknown_or_incomplete" or item.get("replay_allowed") is not False or item.get("temporary_files") != [".request.json.tmp"] for item in statuses): errors.append("STATUS_CONTRACT_MISMATCH")
    if any(item.get("exit_code") != 2 for item in raw.get("statuses", [])): errors.append("STATUS_EXIT_MISMATCH")
    if raw.get("child_exit") != 29 or raw.get("marker_exists") is not False: errors.append("CRASH_OR_MARKER_MISMATCH")
    try:
        reuse = json.loads(raw["reuse_stdout"])
    except Exception:
        reuse = {}
        errors.append("REUSE_JSON_INVALID")
    if raw.get("reuse_exit") != 2 or reuse.get("error") != "REQUEST_PERSISTENCE_FAILED" or reuse.get("operation_invoked") is not False: errors.append("REUSE_CONTRACT_MISMATCH")
    inputs = evidence / "inputs"
    input_hashes = {p.name: sha(p.read_bytes()) for p in sorted(inputs.iterdir()) if p.is_file()}
    if input_hashes != {"program.json":"a7011c4731c99880f181f4d980c5bbe62f563460f1c0aa0d15c83c3dfc91c2ca", "targets.json":"4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"}: errors.append("INPUT_HASH_MISMATCH")
    if raw.get("errors") != [] or raw.get("disposition") != "PASS_SCOPED_REQUEST_TEMP_UNKNOWN_NO_REPLAY": errors.append("RUNNER_RESULT_NOT_PASS")
    result = {"schema":"agent-interface/issue3752-request-temp-crash-audit-v3", "allocation":"issue3752-request-temp-crash-audit-successor-03",
              "formal_allocation":"issue3752-request-temp-crash-successor-02", "raw_sha256":sha(raw_bytes),
              "attempt_blob":blob(attempt_bytes), "cli_blob":blob(cli_bytes), "runner_sha256":sha(runner_bytes),
              "input_sha256":input_hashes, "observed_snapshot":actual, "errors":errors,
              "disposition":"PASS_AUDIT_V3" if not errors else "FAIL_AUDIT_V3"}
    (output / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"disposition":result["disposition"], "errors":errors}, sort_keys=True))
    if errors: raise SystemExit(1)


if __name__ == "__main__":
    main()

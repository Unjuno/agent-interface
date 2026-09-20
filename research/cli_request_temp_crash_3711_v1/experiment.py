"""One-shot request-temp crash probe for Issue #3752; not yet executed."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

EXPECTED_ATTEMPT_SHA256 = "70cc62b450c8b9c8aaa0db49b1e116388368fe4c"
CHILD = r'''
import os
import sys
from pathlib import Path
from unittest.mock import patch
from runtime.cli_v1.attempt import invoke

root = Path(sys.argv[1])
marker = Path(sys.argv[2])
original_open = Path.open

class ExitAfterPrefix:
    def __init__(self, stream):
        self.stream = stream
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return self.stream.__exit__(*args)
    def write(self, data):
        self.stream.write(data[:max(1, len(data) // 2)])
        self.stream.flush()
        os._exit(29)
    def __getattr__(self, name):
        return getattr(self.stream, name)

def patched_open(path, mode="r", *args, **kwargs):
    stream = original_open(path, mode, *args, **kwargs)
    if Path(path).name == ".request.json.tmp" and "x" in mode:
        return ExitAfterPrefix(stream)
    return stream

with patch.object(Path, "open", new=patched_open):
    invoke(lambda **kwargs: marker.write_text("backend-called"),
           {}, root, operation="dispatch")
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


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
    source = Path(os.environ["SOURCE_ROOT"]).resolve()
    output = Path(sys.argv[1]).resolve()
    attempt_source = source / "runtime/cli_v1/attempt.py"
    observed_source_sha256 = sha(attempt_source.read_bytes())
    if observed_source_sha256 != EXPECTED_ATTEMPT_SHA256:
        raise SystemExit("STOP_FROZEN_SOURCE_MISMATCH")
    if output.exists() and any(output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    output.mkdir(parents=True, exist_ok=True)

    run = output / "attempt"
    marker = output / "backend-called"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(source)
    child = subprocess.run(
        [sys.executable, "-c", CHILD, str(run), str(marker)],
        cwd=source, env=env, capture_output=True, timeout=15)
    before = snapshot(run)
    status_rows = []
    status_snapshots = []
    for _ in range(2):
        status = subprocess.run(
            [sys.executable, "-m", "runtime.cli_v1", "attempt-status",
             "--run-directory", str(run)],
            cwd=source, env=env, capture_output=True, timeout=15)
        status_rows.append({
            "exit_code": status.returncode,
            "stdout": status.stdout.decode("utf-8", errors="replace"),
            "stderr": status.stderr.decode("utf-8", errors="replace")})
        status_snapshots.append(snapshot(run))

    from runtime.cli_v1.attempt import invoke
    retry = Mock()
    retry_result, retry_retention = invoke(retry, {}, run, operation="dispatch")
    after = snapshot(run)
    temp = run / ".request.json.tmp"
    expected_request = {
        "schema": "agent-interface/cli-attempt-v1",
        "operation": "dispatch",
        "arguments": {"capture_directory": str(run / "images")},
        "note": "Request existence does not establish invocation or completion. "
                "Missing report means unknown outcome; never automatically replay."}
    expected_bytes = json.dumps(expected_request, allow_nan=False).encode("utf-8")
    temp_bytes = temp.read_bytes() if temp.exists() else b""
    try:
        rows = [json.loads(item["stdout"]) for item in status_rows]
    except Exception:
        rows = []
    errors = []
    if child.returncode != 29:
        errors.append("CHILD_EXIT_NOT_INJECTED_29")
    if marker.exists():
        errors.append("BACKEND_MARKER_EXISTS")
    if (run / "request.json").exists() or (run / "report.json").exists():
        errors.append("FINAL_RECORD_EXISTS")
    if not temp_bytes or not expected_bytes.startswith(temp_bytes) or len(temp_bytes) >= len(expected_bytes):
        errors.append("TEMP_NOT_STRICT_EXPECTED_PREFIX")
    if len(rows) != 2 or any(
            row.get("status") != "unknown_or_incomplete"
            or row.get("replay_allowed") is not False
            or row.get("temporary_files") != [".request.json.tmp"]
            for row in rows):
        errors.append("STATUS_NOT_UNKNOWN_NO_REPLAY_TEMP_VISIBLE")
    if any(row != before for row in status_snapshots) or after != before:
        errors.append("READ_OR_REUSE_CHANGED_SNAPSHOT")
    if retry.called or retry_result.get("error") != "REQUEST_PERSISTENCE_FAILED":
        errors.append("RUN_DIRECTORY_REUSE_NOT_REFUSED")
    disposition = "PASS_REQUEST_TEMP_CRASH_VISIBLE_NO_REPLAY" if not errors else "FAIL"
    result = {
        "issue": 3752,
        "allocation": "issue3752-request-temp-crash-01",
        "disposition": disposition,
        "source_sha256": observed_source_sha256,
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "child_exit_code": child.returncode,
        "backend_marker_exists": marker.exists(),
        "temp_bytes": len(temp_bytes),
        "temp_sha256": sha(temp_bytes) if temp_bytes else None,
        "status_rows": status_rows,
        "retry_called": retry.called,
        "retry_result": retry_result,
        "retry_retention": retry_retention,
        "snapshot_before": before,
        "snapshot_after_each_status": status_snapshots,
        "snapshot_after_reuse": after,
        "errors": errors}
    (output / "raw.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation": result["allocation"],
                      "disposition": disposition, "errors": errors}, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

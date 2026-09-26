"""One-shot successor allocation for Issue #3752; no formal run before freeze."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ALLOCATION = "issue3752-request-temp-crash-successor-02"
BASE = "76965311d899815174b5ed081ff439bd4533ef63"
ATTEMPT_BLOB = "70cc62b450c8b9c8aaa0db49b1e116388368fe4c"
CLI_BLOB = "8a9178b7b8721b8a5471fabcfbeb1cb55976980c"

CRASH_CHILD = r'''
import os, sys
from pathlib import Path
from unittest.mock import patch
from runtime.cli_v1.attempt import invoke
root = Path(sys.argv[1]); marker = Path(sys.argv[2])
open0 = Path.open
class PrefixExit:
    def __init__(self, stream): self.stream = stream
    def __enter__(self): return self
    def __exit__(self, *args): return self.stream.__exit__(*args)
    def write(self, data):
        n = max(1, len(data) // 2)
        self.stream.write(data[:n]); self.stream.flush(); os._exit(29)
    def __getattr__(self, name): return getattr(self.stream, name)
def patched(path, mode="r", *args, **kwargs):
    stream = open0(path, mode, *args, **kwargs)
    if Path(path).name == ".request.json.tmp" and "x" in mode:
        return PrefixExit(stream)
    return stream
with patch.object(Path, "open", new=patched):
    invoke(lambda **kw: marker.write_text("backend-called"), {}, root, operation="dispatch")
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def snapshot(root):
    rows = {}
    if root.exists():
        for p in sorted(root.rglob("*")):
            rel = p.relative_to(root).as_posix()
            rows[rel] = ({"kind": "directory"} if p.is_dir() else
                         {"kind": "file", "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())})
    return rows


def cli(source, env, *args):
    return subprocess.run([sys.executable, "-m", "runtime.cli_v1", *map(str, args)],
                          cwd=source, env=env, capture_output=True, timeout=20)


CLI_REUSE_CHILD = r'''
import sys
from pathlib import Path
from unittest.mock import patch
import runtime.cli_v1.__main__ as entry
marker = Path(sys.argv[1])
argv = sys.argv[2:]
with patch.object(entry, "dispatch", new=lambda **kw: marker.write_text("backend-called")):
    sys.argv = ["agent-interface", *argv]
    raise SystemExit(entry.main())
'''


def main():
    source = Path(os.environ["SOURCE_ROOT"]).resolve()
    output = Path(sys.argv[1]).resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    output.mkdir(parents=True, exist_ok=True)
    attempt = (source / "runtime/cli_v1/attempt.py").read_bytes()
    cli_source = (source / "runtime/cli_v1/__main__.py").read_bytes()
    if blob(attempt) != ATTEMPT_BLOB or blob(cli_source) != CLI_BLOB:
        raise SystemExit("STOP_FROZEN_SOURCE_MISMATCH")
    env = dict(os.environ, PYTHONPATH=str(source))
    run = output / "attempt"
    marker_path = output / "backend-called"
    child = subprocess.run([sys.executable, "-c", CRASH_CHILD, str(run), str(marker_path)],
                           cwd=source, env=env, capture_output=True, timeout=20)
    before = snapshot(run)
    statuses = []
    status_snaps = []
    for _ in range(2):
        result = cli(source, env, "attempt-status", "--run-directory", run)
        statuses.append({"exit_code": result.returncode,
                         "stdout": result.stdout.decode("utf-8", "replace"),
                         "stderr": result.stderr.decode("utf-8", "replace")})
        status_snaps.append(snapshot(run))

    program = output / "program.json"
    targets = output / "targets.json"
    program.write_text(json.dumps({"schema": "agent-interface/action-program-v1", "steps": []}))
    targets.write_text(json.dumps([]))
    # CLI arguments are deliberately valid. Existing run directory must be refused in invoke
    # before dispatch; the missing/invalid program is never reached by the backend.
    reused = subprocess.run([sys.executable, "-c", CLI_REUSE_CHILD, str(marker_path),
                             "dispatch", "--program", str(program), "--targets", str(targets),
                             "--current-observation-seq", "1", "--current-binding-revision", "1",
                             "--run-directory", str(run)], cwd=source, env=env,
                            capture_output=True, timeout=20)
    after = snapshot(run)
    try:
        status_values = [json.loads(x["stdout"]) for x in statuses]
        reuse_value = json.loads(reused.stdout)
    except Exception:
        status_values, reuse_value = [], {}
    temp = (run / ".request.json.tmp").read_bytes()
    expected = {
        "schema": "agent-interface/cli-attempt-v1", "operation": "dispatch",
        "arguments": {"program": json.loads(program.read_text()), "targets": json.loads(targets.read_text()),
                      "current_observation_seq": 1, "current_binding_revision": 1,
                      "display_name": None, "capture_directory": str(run / "images")},
        "note": "Request existence does not establish invocation or completion. Missing report means unknown outcome; never automatically replay."}
    # Crash allocation uses its own simple invoke request; bind the exact actual prefix from that frozen request shape.
    child_request = {
        "schema": "agent-interface/cli-attempt-v1", "operation": "dispatch",
        "arguments": {"capture_directory": str(run / "images")},
        "note": expected["note"]}
    expected_bytes = json.dumps(child_request, allow_nan=False).encode()
    errors = []
    if child.returncode != 29: errors.append("CHILD_EXIT_NOT_29")
    if not temp or not expected_bytes.startswith(temp) or len(temp) >= len(expected_bytes): errors.append("TEMP_NOT_STRICT_EXPECTED_PREFIX")
    if (run / "request.json").exists() or (run / "report.json").exists(): errors.append("FINAL_RECORD_EXISTS")
    if marker_path.exists(): errors.append("BACKEND_MARKER_EXISTS")
    if len(status_values) != 2 or any(v.get("status") != "unknown_or_incomplete" or v.get("replay_allowed") is not False or v.get("temporary_files") != [".request.json.tmp"] for v in status_values): errors.append("STATUS_CONTRACT_MISMATCH")
    if any(s["exit_code"] != 2 for s in statuses): errors.append("STATUS_EXIT_MISMATCH")
    if any(s != before for s in status_snaps) or after != before: errors.append("SNAPSHOT_MUTATED")
    if reused.returncode != 2 or reuse_value.get("error") != "REQUEST_PERSISTENCE_FAILED" or reuse_value.get("operation_invoked") is not False: errors.append("CLI_REUSE_NOT_REFUSED")
    if reuse_value.get("retention", {}).get("request_persisted") is not False: errors.append("CLI_REUSE_RETENTION_MISMATCH")
    result = {"schema": "agent-interface/issue3752-request-temp-crash-raw-v2", "allocation": ALLOCATION,
              "base": BASE, "attempt_blob": blob(attempt), "attempt_sha256": sha(attempt),
              "cli_blob": blob(cli_source), "cli_sha256": sha(cli_source),
              "runner_sha256": sha(Path(__file__).read_bytes()), "child_exit": child.returncode,
              "temp_bytes": len(temp), "temp_sha256": sha(temp), "statuses": statuses,
              "reuse_exit": reused.returncode, "reuse_stdout": reused.stdout.decode("utf-8", "replace"),
              "reuse_stderr": reused.stderr.decode("utf-8", "replace"), "marker_exists": marker_path.exists(),
              "snapshot_before": before, "snapshot_after_status": status_snaps,
              "snapshot_after_reuse": after, "errors": errors,
              "disposition": "PASS_SCOPED_REQUEST_TEMP_UNKNOWN_NO_REPLAY" if not errors else "FAIL"}
    (output / "raw.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation": ALLOCATION, "disposition": result["disposition"], "errors": errors}, sort_keys=True))
    if errors: raise SystemExit(1)


if __name__ == "__main__":
    main()

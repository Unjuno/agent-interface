"""One-shot Issue #3711 downstream truncation experiment, allocation 02."""
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys
from unittest.mock import patch


def digest(data):
    return hashlib.sha256(data).hexdigest()


class FullAcceptThenTruncate:
    def __init__(self, limit=23):
        self.limit = limit
        self.accepted = []
        self.delivered = bytearray()
        self.return_values = []

    def write(self, text):
        self.accepted.append(text)
        self.delivered.extend(text.encode("utf-8")[:self.limit])
        count = len(text)
        self.return_values.append(count)
        return count

    def flush(self):
        return None


def file_snapshot(root):
    snapshot = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_file():
            snapshot[name] = {"kind": "file", "sha256": digest(path.read_bytes()),
                              "bytes": path.stat().st_size}
        elif path.is_dir():
            snapshot[name] = {"kind": "directory"}
    return snapshot


def main():
    source = Path(os.environ["SOURCE_ROOT"]).resolve()
    output = Path(sys.argv[1]).resolve()
    here = Path(__file__).resolve().parent
    freeze_path = here / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text())
    names = list(freeze["sha256"])
    observed = {}
    for name in names:
        path = (source / name) if name.startswith("runtime/") else (here / name)
        observed[name] = digest(path.read_bytes())
    if observed != freeze["sha256"]:
        raise SystemExit("STOP_FREEZE_HASH_MISMATCH")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    sys.path.insert(0, str(source))
    from runtime.cli_v1 import __main__ as cli

    run = output / "attempt"
    program = output / "program.json"
    targets = output / "targets.json"
    program.write_text("{}\n")
    targets.write_text("{}\n")
    calls = []
    def synthetic_backend(**kwargs):
        calls.append(kwargs)
        request = json.loads((run / "request.json").read_bytes())
        if request.get("arguments") != kwargs:
            raise AssertionError("persisted request differs from backend arguments")
        if (run / "report.json").exists():
            raise AssertionError("report exists before backend return")
        return {"schema": "agent-interface/runtime-dispatch-result-v1",
                "status": "returned",
                "result": {"status": "completed", "scope": "synthetic-only"}}

    sink = FullAcceptThenTruncate()
    old_argv = sys.argv
    try:
        sys.argv = ["agent-interface", "dispatch", "--program", str(program),
                    "--targets", str(targets), "--current-observation-seq", "1",
                    "--current-binding-revision", "0", "--run-directory", str(run)]
        with patch.object(sys, "stdout", sink), patch.object(cli, "dispatch", side_effect=synthetic_backend):
            producer_exit = cli.main()
    finally:
        sys.argv = old_argv

    accepted = "".join(sink.accepted).encode("utf-8")
    delivered = bytes(sink.delivered)
    try:
        json.loads(delivered)
        consumer = {"accepted": True, "error_type": None}
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        consumer = {"accepted": False, "error_type": type(error).__name__, "error": str(error)}

    before = file_snapshot(run)
    request = (run / "request.json").read_bytes()
    report = (run / "report.json").read_bytes()
    recovery_stream = io.StringIO()
    try:
        sys.argv = ["agent-interface", "attempt-status", "--run-directory", str(run)]
        with patch.object(sys, "stdout", recovery_stream), patch.object(cli, "dispatch", side_effect=synthetic_backend):
            recovery_exit = cli.main()
    finally:
        sys.argv = old_argv
    after = file_snapshot(run)
    recovery = recovery_stream.getvalue().encode("utf-8")

    (output / "accepted.json").write_bytes(accepted)
    (output / "delivered-prefix.bin").write_bytes(delivered)
    (output / "request.json").write_bytes(request)
    (output / "report.json").write_bytes(report)
    (output / "recovery.stdout").write_bytes(recovery)
    raw = {
        "allocation": freeze["allocation"], "base_commit": freeze["base_commit"],
        "image_digest": freeze["image_digest"], "freeze_sha256": digest(freeze_path.read_bytes()),
        "source_sha256": observed, "python": sys.version, "platform": platform.platform(),
        "machine": platform.machine(), "engine_platform": os.environ.get("ENGINE_PLATFORM", "not-recorded"),
        "producer": {"write_return_values": sink.return_values,
                     "reported_character_count": len(accepted.decode("utf-8")),
                     "accepted_sha256": digest(accepted), "cli_exit_code": producer_exit},
        "downstream": {"delivered_bytes": len(delivered), "delivered_sha256": digest(delivered),
                       "strict_prefix": accepted.startswith(delivered) and len(delivered) < len(accepted),
                       "consumer": consumer},
        "dispatch_call_count_after_recovery": len(calls),
        "request_sha256_before_recovery": digest(request), "report_sha256_before_recovery": digest(report),
        "attempt_files_before_recovery": before, "attempt_files_after_recovery": after,
        "request_sha256_after_recovery": digest((run / "request.json").read_bytes()),
        "report_sha256_after_recovery": digest((run / "report.json").read_bytes()),
        "recovery_exit_code": recovery_exit, "recovery_stdout_sha256": digest(recovery),
    }
    (output / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation": freeze["allocation"], "runner": "completed",
                      "write_return_values": sink.return_values,
                      "delivered_bytes": len(delivered), "consumer": consumer,
                      "dispatch_calls_after_recovery": len(calls)}, sort_keys=True))


if __name__ == "__main__":
    main()

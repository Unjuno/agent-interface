"""One-shot bounded downstream-truncation probe for Issue #3711."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from unittest.mock import patch


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FullAcceptTruncatingSink:
    """Producer sees a full accepted write; the downstream receives a prefix."""
    def __init__(self, delivered_bytes=23):
        self.limit = delivered_bytes
        self.accepted = []
        self.delivered = bytearray()
        self.calls = 0
        self.reported_counts = []

    def write(self, text):
        self.calls += 1
        self.accepted.append(text)
        self.delivered.extend(text.encode("utf-8")[:self.limit])
        reported = len(text)
        self.reported_counts.append(reported)
        return reported

    def flush(self):
        return None


def snapshot(root):
    return {
        path.name: {"sha256": sha(path.read_bytes()), "bytes": path.stat().st_size}
        for path in sorted(root.iterdir()) if path.is_file()
    }


def main():
    source = Path(os.environ["SOURCE_ROOT"]).resolve()
    output = Path(sys.argv[1]).resolve()
    freeze_path = Path(__file__).with_name("FREEZE.json")
    freeze = json.loads(freeze_path.read_text())
    runtime_attempt = source / "runtime/cli_v1/attempt.py"
    runtime_cli = source / "runtime/cli_v1/__main__.py"
    script = Path(__file__).resolve()
    sources = {
        "runtime/cli_v1/attempt.py": sha(runtime_attempt.read_bytes()),
        "runtime/cli_v1/__main__.py": sha(runtime_cli.read_bytes()),
        "experiment.py": sha(script.read_bytes()),
        "audit.py": sha(script.with_name("audit.py").read_bytes()),
        "PLAN.md": sha(script.with_name("PLAN.md").read_bytes()),
    }
    if sources != freeze["sha256"]:
        raise SystemExit("STOP_FREEZE_HASH_MISMATCH")
    if output.exists() and any(output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    output.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(source))
    from runtime.cli_v1 import __main__ as cli

    attempt_dir = output / "attempt"
    program = output / "program.json"
    targets = output / "targets.json"
    program.write_text("{}\n")
    targets.write_text("{}\n")
    sink = FullAcceptTruncatingSink()
    dispatch_calls = []
    original_argv = [
        "agent-interface", "dispatch", "--program", str(program),
        "--targets", str(targets), "--current-observation-seq", "1",
        "--current-binding-revision", "0", "--run-directory", str(attempt_dir),
    ]
    result = {"allocation": freeze["allocation"], "base_commit": freeze["base_commit"],
              "image_digest": freeze["image_digest"], "freeze_sha256": sha(freeze_path.read_bytes()),
              "source_sha256": sources,
              "python": sys.version, "platform": platform.platform(),
              "engine_platform": os.environ.get("ENGINE_PLATFORM", "not-recorded")}

    def backend(**kwargs):
        dispatch_calls.append(kwargs)
        request = json.loads((attempt_dir / "request.json").read_bytes())
        if request.get("arguments") != kwargs:
            raise AssertionError("persisted request differed from backend arguments")
        if (attempt_dir / "report.json").exists():
            raise AssertionError("report existed before backend returned")
        return {"schema": "agent-interface/runtime-dispatch-result-v1",
                "status": "returned",
                "result": {"status": "completed", "scope": "synthetic-only"}}

    old_argv = sys.argv
    try:
        sys.argv = original_argv
        with patch.object(sys, "stdout", sink), patch.object(cli, "dispatch", side_effect=backend):
            cli_exit_code = cli.main()
    finally:
        sys.argv = old_argv

    accepted_text = "".join(sink.accepted)
    delivered = bytes(sink.delivered)
    try:
        json.loads(delivered)
        consumer = {"accepted": True, "error": None}
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        consumer = {"accepted": False, "error_type": type(error).__name__, "error": str(error)}

    before = snapshot(attempt_dir)
    request_bytes = (attempt_dir / "request.json").read_bytes()
    report_bytes = (attempt_dir / "report.json").read_bytes()
    recovery_stream = __import__("io").StringIO()
    old_argv = sys.argv
    try:
        sys.argv = ["agent-interface", "attempt-status", "--run-directory", str(attempt_dir)]
        with patch.object(sys, "stdout", recovery_stream), patch.object(cli, "dispatch", side_effect=backend):
            recovery_exit_code = cli.main()
    finally:
        sys.argv = old_argv
    after = snapshot(attempt_dir)
    recovery_text = recovery_stream.getvalue()

    (output / "request.json").write_bytes(request_bytes)
    (output / "report.json").write_bytes(report_bytes)
    (output / "accepted.json").write_text(accepted_text)
    (output / "delivered-prefix.bin").write_bytes(delivered)
    (output / "recovery.stdout").write_text(recovery_text)
    result.update({
        "producer": {"write_calls": sink.calls, "reported_character_count": len(accepted_text),
                     "write_return_values": sink.reported_counts,
                     "delivered_byte_count": len(delivered), "accepted_sha256": sha(accepted_text.encode()),
                     "delivered_sha256": sha(delivered), "strict_prefix": accepted_text.encode().startswith(delivered)
                     and len(delivered) < len(accepted_text.encode()), "cli_exit_code": cli_exit_code},
        "downstream_consumer": consumer,
        "dispatch_call_count_after_recovery": len(dispatch_calls),
        "request_sha256_before_recovery": sha(request_bytes),
        "report_sha256_before_recovery": sha(report_bytes),
        "attempt_files_before_recovery": before,
        "attempt_files_after_recovery": after,
        "request_sha256_after_recovery": sha((attempt_dir / "request.json").read_bytes()),
        "report_sha256_after_recovery": sha((attempt_dir / "report.json").read_bytes()),
        "recovery_exit_code": recovery_exit_code,
        "recovery_stdout_sha256": sha(recovery_text.encode()),
    })
    (output / "raw.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()

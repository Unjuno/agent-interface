"""Persist one command's attempt and direct-file streams; no shell or retries."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    here = Path(__file__).resolve().parent
    sources = {path.name: sha(path.read_bytes()) for path in sorted(here.glob("*.py"))}
    receipt = {
        "purpose": args.purpose, "argv": command, "cwd": str(Path.cwd()),
        "started_utc": now(), "host_platform": platform.platform(),
        "runner_python": sys.version, "source_sha256": sources, "retries": 0,
        "attempt_state": "ATTEMPT_STARTED", "timed_out": False, "interrupted": False,
    }
    initial = json.dumps(receipt, indent=2) + "\n"
    (output / "attempt.json").write_text(initial, encoding="utf-8")
    (output / "receipt.json").write_text(initial, encoding="utf-8")
    with (output / "stdout.txt").open("xb") as out, (output / "stderr.txt").open("xb") as err:
        try:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        except OSError as error:
            err.write(str(error).encode("utf-8"))
            code = 127
            receipt.update(launch_error=type(error).__name__, attempt_state="LAUNCH_FAILED")
        else:
            receipt["pid"] = process.pid
            try:
                process.wait(timeout=args.timeout)
                receipt["attempt_state"] = "COMPLETED"
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
                receipt["timed_out"] = isinstance(error, subprocess.TimeoutExpired)
                receipt["interrupted"] = isinstance(error, KeyboardInterrupt)
                receipt["attempt_state"] = "TIMED_OUT" if receipt["timed_out"] else "INTERRUPTED"
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
            code = process.returncode
    stdout = (output / "stdout.txt").read_bytes()
    stderr = (output / "stderr.txt").read_bytes()
    receipt.update(ended_utc=now(), exit_code=code,
                   stdout_sha256=sha(stdout), stderr_sha256=sha(stderr))
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    print(json.dumps({"output": str(output), "exit_code": code, "purpose": args.purpose}))
    return 130 if receipt["interrupted"] else 124 if receipt["timed_out"] else code


if __name__ == "__main__":
    raise SystemExit(main())

"""Capture one command's raw streams and receipt without a shell or retries."""
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
    }
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        receipt["pid"] = process.pid
        try:
            stdout, stderr = process.communicate(timeout=args.timeout)
            receipt["timed_out"] = False
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            receipt["timed_out"] = True
        code = process.returncode
    except OSError as error:
        stdout, stderr, code = b"", str(error).encode("utf-8"), 127
        receipt["launch_error"] = type(error).__name__
    receipt.update(ended_utc=now(), exit_code=code,
                   stdout_sha256=sha(stdout), stderr_sha256=sha(stderr))
    (output / "stdout.txt").write_bytes(stdout)
    (output / "stderr.txt").write_bytes(stderr)
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    print(json.dumps({"output": str(output), "exit_code": code, "purpose": args.purpose}))
    return code if not receipt.get("timed_out") else 124


if __name__ == "__main__":
    raise SystemExit(main())


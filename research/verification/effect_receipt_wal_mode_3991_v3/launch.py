"""Host-side, receipt-producing OrbStack/Docker launcher for #4945 allocation 03."""
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

IMAGE = "sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419"
SOURCE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def docker_command(kind, evidence, audit_output=None):
    common = ["docker", "run", "--rm", "--pull=never", "--platform=linux/amd64",
              "--network=none", "--read-only", "--cpus=1", "--memory=1g",
              "--pids-limit=32", "--security-opt=no-new-privileges", "--tmpfs",
              "/tmp:rw,noexec,nosuid,size=64m", "--mount",
              f"type=bind,source={SOURCE},target=/src,readonly"]
    if kind in ("construction", "formal"):
        common += ["--mount", f"type=bind,source={evidence},target=/out",
                   "--workdir", "/src", "--env", f"ALLOC_IMAGE_ID={IMAGE}",
                   IMAGE, "python", "/src/runner.py", kind, "/out"]
    elif kind in ("audit-construction", "audit-formal"):
        phase = kind.removeprefix("audit-")
        common += ["--mount", f"type=bind,source={evidence},target=/evidence,readonly",
                   "--mount", f"type=bind,source={audit_output},target=/audit",
                   "--workdir", "/src", IMAGE, "python", "/src/audit.py",
                   "/evidence", "/audit/AUDIT.json", phase]
    else:
        raise ValueError("unknown_stage")
    return common


def main(argv):
    if len(argv) not in (2, 3):
        raise SystemExit("usage: launch.py construction|formal OUT_DIR | audit-construction|audit-formal EVIDENCE_DIR AUDIT_DIR")
    kind = argv[0]
    evidence = Path(argv[1]).resolve()
    if kind.startswith("audit-"):
        if len(argv) != 3:
            raise SystemExit("audit requires EVIDENCE_DIR and AUDIT_DIR")
        audit_output = Path(argv[2]).resolve()
        if not evidence.is_dir() or not audit_output.is_dir() or any(audit_output.iterdir()):
            raise SystemExit("STOP_AUDIT_PATH_NOT_FRESH")
        receipt_dir = audit_output
    else:
        audit_output = None
        if len(argv) != 2 or evidence.exists():
            raise SystemExit("STOP_OUTPUT_PATH_NOT_FRESH")
        evidence.mkdir(parents=True)
        receipt_dir = evidence
    command = docker_command(kind, evidence, audit_output)
    started_at = utc_now()
    started_ns = time.monotonic_ns()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    ended_ns = time.monotonic_ns()
    receipt = {"stage": kind, "image_id": IMAGE, "source_dir": str(SOURCE),
               "evidence_dir": str(evidence), "audit_output_dir": str(audit_output) if audit_output else None,
               "command_argv": command, "pid": process.pid, "exit_code": process.returncode,
               "start_utc": started_at, "end_utc": utc_now(), "elapsed_ns": ended_ns - started_ns,
               "stdout_bytes": len(stdout), "stdout_sha256": sha(stdout),
               "stderr_bytes": len(stderr), "stderr_sha256": sha(stderr)}
    (receipt_dir / "DOCKER.stdout.bin").write_bytes(stdout)
    (receipt_dir / "DOCKER.stderr.bin").write_bytes(stderr)
    (receipt_dir / "INVOCATION.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                                                   encoding="utf-8")
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    print(json.dumps({"stage": kind, "exit_code": process.returncode,
                      "pid": process.pid, "elapsed_ns": ended_ns - started_ns,
                      "stdout_sha256": receipt["stdout_sha256"],
                      "stderr_sha256": receipt["stderr_sha256"]}, sort_keys=True))
    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main(sys.argv[1:])

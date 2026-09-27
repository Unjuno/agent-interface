"""One-shot local Docker orchestration for Issue #4621."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

ALLOCATION = "needle-online-snapshot-cadence-4621-v2"
IMAGE = "needle-pilot05:local"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
LIMITS = ["--pull=never", "--platform", "linux/amd64", "--network", "none", "--read-only",
          "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m", "--pids-limit", "64", "--memory", "2g", "--cpus", "1"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(path, target, readonly):
    value = f"type=bind,source={Path(path).resolve().as_posix()},target={target}"
    return value + (",readonly" if readonly else "")


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")


def docker_command(image_id, source, output, script, args):
    return ["docker", "run", "--rm", *LIMITS,
            "--mount", bind(source, "/src", True),
            "--mount", bind(output, "/out", False),
            "--workdir", "/src", "--entrypoint", "python", image_id, "-B", script, *args]


def stop(output, phase, detail, formal_invocations):
    write_new(output / "STOP.json", {"schema": "needle-snapshot-cadence-stop-v1", "status": "STOP",
                                     "phase": phase, "detail": detail,
                                     "formal_invocations": formal_invocations, "retry_count": 0})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--train-timeout-s", type=int, default=1800)
    parser.add_argument("--audit-timeout-s", type=int, default=600)
    args = parser.parse_args()
    source, output = Path(args.source).resolve(), Path(args.out).resolve()
    if not source.is_dir() or not output.is_dir() or any(output.iterdir()):
        raise SystemExit("source_must_exist_and_output_root_must_be_empty")
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    freeze_sha = digest(source / "FREEZE.json")
    if freeze.get("allocation") != ALLOCATION or freeze.get("issue") != 4621:
        stop(output, "freeze_identity", "allocation_or_issue_mismatch", 0)
        return 2
    if (source / "FREEZE.sha256").read_text(encoding="ascii").strip() != freeze_sha:
        stop(output, "freeze_sidecar", "freeze_sha256_mismatch", 0)
        return 2
    for relative, expected in freeze["source_sha256"].items():
        if digest(source / relative) != expected:
            stop(output, "source_hash", relative, 0)
            return 2
    if (freeze.get("construction", {}).get("image_id") != IMAGE_ID
            or freeze.get("runtime", {}).get("network") != "none"
            or freeze.get("runtime", {}).get("root_read_only") is not True):
        stop(output, "freeze_environment", "pinned runtime fields do not match", 0)
        return 2
    image_info = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE],
                                capture_output=True, text=True, check=False, timeout=30)
    if image_info.returncode != 0 or image_info.stdout.strip() != IMAGE_ID:
        stop(output, "image_preflight", {"stdout": image_info.stdout, "stderr": image_info.stderr,
                                         "expected": IMAGE_ID}, 0)
        return 2
    docker_info = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"],
                                 capture_output=True, text=True, check=False, timeout=30)
    if docker_info.returncode != 0:
        stop(output, "docker_daemon_preflight", {"stdout": docker_info.stdout, "stderr": docker_info.stderr}, 0)
        return 2

    training_dir = output / "training"
    training_dir.mkdir()
    training_command = docker_command(IMAGE_ID, source, output, "runner.py", ["--out", "/out/training"])
    audit_command = docker_command(IMAGE_ID, source, output, "audit.py", ["--source", "/src", "--out", "/out"])
    invocation = {"schema": "needle-snapshot-cadence-invocation-v1", "allocation": ALLOCATION,
                  "issue": 4621, "freeze_sha256": freeze_sha, "source_sha256": freeze["source_sha256"],
                  "docker_image": IMAGE, "docker_image_id": IMAGE_ID,
                  "docker_server_version": docker_info.stdout.strip(), "network": "none",
                  "root_read_only": True, "source_read_only": True, "formal_invocations": 1,
                  "training_container_invocations": 1, "audit_container_invocations": 1,
                  "retry_count": 0, "training_timeout_s": args.train_timeout_s,
                  "audit_timeout_s": args.audit_timeout_s, "started_ns": time.time_ns(),
                  "training_command": training_command, "audit_command": audit_command}
    write_new(output / "FORMAL_INVOCATION.json", invocation)
    try:
        training = subprocess.run(training_command, cwd=source, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", check=False,
                                  timeout=args.train_timeout_s)
    except subprocess.TimeoutExpired as exc:
        (output / "training.stdout.txt").write_text(exc.stdout or "", encoding="utf-8", newline="\n")
        (output / "training.stderr.txt").write_text(exc.stderr or "", encoding="utf-8", newline="\n")
        stop(output, "training_timeout", {"timeout_s": args.train_timeout_s}, 1)
        return 124
    (output / "training.stdout.txt").write_text(training.stdout, encoding="utf-8", newline="\n")
    (output / "training.stderr.txt").write_text(training.stderr, encoding="utf-8", newline="\n")
    if training.returncode != 0:
        stop(output, "training_container", {"exit_code": training.returncode,
             "stdout_sha256": hashlib.sha256(training.stdout.encode()).hexdigest(),
             "stderr_sha256": hashlib.sha256(training.stderr.encode()).hexdigest()}, 1)
        return training.returncode or 2
    try:
        audit = subprocess.run(audit_command, cwd=source, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", check=False,
                               timeout=args.audit_timeout_s)
    except subprocess.TimeoutExpired as exc:
        (output / "audit.stdout.txt").write_text(exc.stdout or "", encoding="utf-8", newline="\n")
        (output / "audit.stderr.txt").write_text(exc.stderr or "", encoding="utf-8", newline="\n")
        stop(output, "audit_timeout", {"timeout_s": args.audit_timeout_s}, 1)
        return 124
    (output / "audit.stdout.txt").write_text(audit.stdout, encoding="utf-8", newline="\n")
    (output / "audit.stderr.txt").write_text(audit.stderr, encoding="utf-8", newline="\n")
    invocation["finished_ns"] = time.time_ns()
    invocation["training_exit_code"] = training.returncode
    invocation["audit_exit_code"] = audit.returncode
    invocation["training_stdout_sha256"] = hashlib.sha256(training.stdout.encode()).hexdigest()
    invocation["training_stderr_sha256"] = hashlib.sha256(training.stderr.encode()).hexdigest()
    invocation["audit_stdout_sha256"] = hashlib.sha256(audit.stdout.encode()).hexdigest()
    invocation["audit_stderr_sha256"] = hashlib.sha256(audit.stderr.encode()).hexdigest()
    # Preserve the initial invocation bytes and write terminal results separately.
    write_new(output / "FORMAL_COMPLETION.json", invocation)
    print(training.stdout, end="")
    print(audit.stdout, end="")
    return audit.returncode


if __name__ == "__main__":
    raise SystemExit(main())

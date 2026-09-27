"""One host orchestration: one training container, then one independent audit container."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

ALLOCATION = "needle-lora-rank1-online-skill-v1"
IMAGE = "needle-pilot05:local"
LIMITS = ["--pull=never", "--platform", "linux/amd64", "--network", "none",
          "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
          "--pids-limit", "64", "--memory", "2g", "--cpus", "1"]


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mount(path, target, readonly=False):
    value = f"type=bind,source={Path(path).resolve().as_posix()},target={target}"
    return value + (",readonly" if readonly else "")


def docker_command(image_id, source, output, script, args):
    return ["docker", "run", "--rm", *LIMITS,
            "--mount", mount(source, "/src", True),
            "--mount", mount(output, "/out", False),
            "--workdir", "/src", "--entrypoint", "python", image_id,
            "-B", script, *args]


def write_new(path, obj):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    source, output = Path(args.source).resolve(), Path(args.out).resolve()
    if not source.is_dir() or not output.is_dir() or any(output.iterdir()):
        raise SystemExit("source_must_exist_and_output_must_be_new_empty_directory")
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("allocation") != ALLOCATION or freeze.get("issue") != 4507:
        raise SystemExit("freeze_identity_mismatch")
    if (source / "FREEZE.sha256").read_text(encoding="ascii").strip() != sha_file(source / "FREEZE.json"):
        raise SystemExit("freeze_sidecar_mismatch")
    for relative, expected in freeze["source_sha256"].items():
        if sha_file(source / relative) != expected:
            raise SystemExit("source_hash_mismatch:" + relative)
    info = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE],
                          capture_output=True, text=True, check=False)
    if info.returncode != 0 or info.stdout.strip() != freeze["docker_image_id"]:
        write_new(output / "STOP.json", {"status": "STOP", "phase": "image_preflight",
                                           "expected": freeze["docker_image_id"],
                                           "observed": info.stdout.strip(), "stderr": info.stderr,
                                           "formal_invocations": 0, "retry_count": 0})
        return 2

    training = docker_command(freeze["docker_image_id"], source, output, "runner.py", ["--out", "/out"])
    audit = docker_command(freeze["docker_image_id"], source, output, "audit.py",
                           ["--source", "/src", "--out", "/out"])
    write_new(output / "FORMAL_INVOCATION.json", {
        "schema": "needle-rank1-formal-invocation.v1", "allocation": ALLOCATION, "issue": 4507,
        "base_main_sha": freeze["base_main_sha"], "started_ns": time.time_ns(),
        "formal_invocations": 1, "training_container_invocations": 1,
        "audit_container_invocations": 1, "retry_count": 0,
        "freeze_sha256": sha_file(source / "FREEZE.json"),
        "source_sha256": freeze["source_sha256"], "docker_image_id": freeze["docker_image_id"],
        "training_command": training, "audit_command": audit,
    })
    train_result = subprocess.run(training, cwd=source, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", check=False)
    (output / "training.stdout.txt").write_text(train_result.stdout, encoding="utf-8", newline="\n")
    (output / "training.stderr.txt").write_text(train_result.stderr, encoding="utf-8", newline="\n")
    if train_result.returncode != 0:
        write_new(output / "STOP.json", {"status": "STOP", "phase": "training_container",
                                           "exit_code": train_result.returncode,
                                           "stdout_sha256": hashlib.sha256(train_result.stdout.encode()).hexdigest(),
                                           "stderr_sha256": hashlib.sha256(train_result.stderr.encode()).hexdigest(),
                                           "formal_invocations": 1, "retry_count": 0})
        print(train_result.stdout, end="")
        print(train_result.stderr, end="")
        return train_result.returncode or 2
    audit_result = subprocess.run(audit, cwd=source, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", check=False)
    (output / "audit.stdout.txt").write_text(audit_result.stdout, encoding="utf-8", newline="\n")
    (output / "audit.stderr.txt").write_text(audit_result.stderr, encoding="utf-8", newline="\n")
    write_new(output / "HOST_CAPTURE.json", {
        "training_exit_code": train_result.returncode, "audit_exit_code": audit_result.returncode,
        "training_stdout_sha256": hashlib.sha256(train_result.stdout.encode()).hexdigest(),
        "training_stderr_sha256": hashlib.sha256(train_result.stderr.encode()).hexdigest(),
        "audit_stdout_sha256": hashlib.sha256(audit_result.stdout.encode()).hexdigest(),
        "audit_stderr_sha256": hashlib.sha256(audit_result.stderr.encode()).hexdigest(),
        "finished_ns": time.time_ns(), "retry_count": 0,
    })
    print(train_result.stdout, end="")
    print(audit_result.stdout, end="")
    return audit_result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

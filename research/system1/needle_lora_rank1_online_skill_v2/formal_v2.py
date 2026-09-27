"""Single v2 orchestration with a dedicated training subdirectory."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

ALLOCATION = "needle-lora-rank1-online-skill-v2"
IMAGE = "needle-pilot05:local"
LIMITS = ["--pull=never", "--platform", "linux/amd64", "--network", "none",
          "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
          "--pids-limit", "64", "--memory", "2g", "--cpus", "1"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(path, target, readonly):
    value = f"type=bind,source={Path(path).resolve().as_posix()},target={target}"
    return value + (",readonly" if readonly else "")


def docker_command(image_id, source, dependency, output, script, args):
    return ["docker", "run", "--rm", *LIMITS,
            "--mount", bind(source, "/src/v2", True),
            "--mount", bind(dependency, "/src/v1", True),
            "--mount", bind(output, "/out", False),
            "--workdir", "/src/v2", "--entrypoint", "python", image_id,
            "-B", script, *args]


def write_new(path, obj):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--dependency", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    source, dependency, output = (Path(args.source).resolve(), Path(args.dependency).resolve(),
                                  Path(args.out).resolve())
    if not source.is_dir() or not dependency.is_dir() or not output.is_dir() or any(output.iterdir()):
        raise SystemExit("source_dependency_must_exist_and_output_root_must_be_empty")
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("allocation") != ALLOCATION or freeze.get("issue") != 4507:
        raise SystemExit("freeze_identity_mismatch")
    freeze_sha = digest(source / "FREEZE.json")
    if (source / "FREEZE.sha256").read_text(encoding="ascii").strip() != freeze_sha:
        raise SystemExit("freeze_sidecar_mismatch")
    for relative, expected in freeze["source_sha256"].items():
        if digest(source / relative) != expected:
            raise SystemExit("source_hash_mismatch:" + relative)
    for relative, expected in freeze["dependency_sha256"].items():
        if digest(dependency / relative) != expected:
            raise SystemExit("dependency_hash_mismatch:" + relative)
    image_info = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE],
                                capture_output=True, text=True, check=False)
    if image_info.returncode != 0 or image_info.stdout.strip() != freeze["docker_image_id"]:
        write_new(output / "STOP.json", {"status": "STOP", "phase": "image_preflight",
                                           "expected": freeze["docker_image_id"],
                                           "observed": image_info.stdout.strip(), "stderr": image_info.stderr,
                                           "formal_invocations": 0, "retry_count": 0})
        return 2

    training_dir = output / "training"
    training_dir.mkdir()
    training = docker_command(freeze["docker_image_id"], source, dependency, output,
                              "runner_v2.py", ["--out", "/out/training"])
    audit = docker_command(freeze["docker_image_id"], source, dependency, output,
                            "audit_v2.py", ["--source", "/src/v2", "--dependency", "/src/v1", "--out", "/out"])
    write_new(output / "FORMAL_INVOCATION.json", {
        "schema": "needle-rank1-formal-invocation-v2.v1", "allocation": ALLOCATION, "issue": 4507,
        "base_main_sha": freeze["base_main_sha"], "parent_evidence_commit": freeze["parent_evidence_commit"],
        "started_ns": time.time_ns(), "formal_invocations": 1,
        "training_container_invocations": 1, "audit_container_invocations": 1,
        "retry_count": 0, "freeze_sha256": freeze_sha,
        "source_sha256": freeze["source_sha256"], "dependency_sha256": freeze["dependency_sha256"],
        "docker_image_id": freeze["docker_image_id"], "training_command": training, "audit_command": audit,
        "output_layout": {"host_metadata": "/out", "training_results": "/out/training"},
    })
    trained = subprocess.run(training, cwd=source, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", check=False)
    (output / "training.stdout.txt").write_text(trained.stdout, encoding="utf-8", newline="\n")
    (output / "training.stderr.txt").write_text(trained.stderr, encoding="utf-8", newline="\n")
    if trained.returncode != 0:
        write_new(output / "STOP.json", {"status": "STOP", "phase": "training_container",
                                           "exit_code": trained.returncode,
                                           "stdout_sha256": hashlib.sha256(trained.stdout.encode()).hexdigest(),
                                           "stderr_sha256": hashlib.sha256(trained.stderr.encode()).hexdigest(),
                                           "formal_invocations": 1, "retry_count": 0})
        print(trained.stdout, end="")
        print(trained.stderr, end="")
        return trained.returncode or 2
    audited = subprocess.run(audit, cwd=source, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", check=False)
    (output / "audit.stdout.txt").write_text(audited.stdout, encoding="utf-8", newline="\n")
    (output / "audit.stderr.txt").write_text(audited.stderr, encoding="utf-8", newline="\n")
    write_new(output / "HOST_CAPTURE.json", {
        "training_exit_code": trained.returncode, "audit_exit_code": audited.returncode,
        "training_stdout_sha256": hashlib.sha256(trained.stdout.encode()).hexdigest(),
        "training_stderr_sha256": hashlib.sha256(trained.stderr.encode()).hexdigest(),
        "audit_stdout_sha256": hashlib.sha256(audited.stdout.encode()).hexdigest(),
        "audit_stderr_sha256": hashlib.sha256(audited.stderr.encode()).hexdigest(),
        "finished_ns": time.time_ns(), "retry_count": 0,
    })
    print(trained.stdout, end="")
    print(audited.stdout, end="")
    return audited.returncode


if __name__ == "__main__":
    raise SystemExit(main())

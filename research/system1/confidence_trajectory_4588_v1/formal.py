"""One-shot host orchestration for runner and independent audit containers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

IMAGE = "needle-pilot05:local"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def docker_base():
    return ["docker", "run", "--rm", "--network", "none", "--read-only",
            "--cpus=1", "--memory=2g", "--pids-limit=64", "--tmpfs",
            "/tmp:rw,nosuid,nodev,size=512m"]


def run_once(cmd):
    started = time.monotonic_ns()
    result = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    return {"returncode": result.returncode,
            "elapsed_ms": (time.monotonic_ns() - started) / 1e6,
            "stdout": result.stdout.decode("utf-8", "replace"),
            "stderr": result.stderr.decode("utf-8", "replace"),
            "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--image-id", required=True)
    args = p.parse_args()
    source = args.source_root.resolve()
    root = args.out.resolve()
    freeze_raw = (source / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_raw)
    if freeze.get("allocation") != "confidence-trajectory-system1-v1":
        raise SystemExit("STOP_FREEZE_IDENTITY")
    if args.image_id != IMAGE_ID or freeze.get("runtime", {}).get("image_id") != IMAGE_ID:
        raise SystemExit("STOP_IMAGE_ID")
    for rel, expected in freeze["source_sha256"].items():
        if sha((source / rel).read_bytes()) != expected:
            raise SystemExit("STOP_SOURCE_HASH:" + rel)
    image = subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
                           capture_output=True, text=True, check=False)
    if image.returncode or image.stdout.strip() != IMAGE_ID:
        raise SystemExit("STOP_PINNED_IMAGE_UNAVAILABLE_OR_MISMATCH")
    if root.exists() and any(root.iterdir()):
        raise SystemExit("STOP_OUTPUT_ROOT_NOT_EMPTY")
    root.mkdir(parents=True, exist_ok=True)
    training, audit_out = root / "training", root / "audit"
    training.mkdir(); audit_out.mkdir()
    source_mount = str(source)
    training_mount = str(training)
    runner_cmd = docker_base() + ["-v", f"{source_mount}:/src:ro", "-v", f"{training_mount}:/out:rw",
                                  "--entrypoint", "python", IMAGE, "/src/runner.py", "--out", "/out"]
    runner_result = run_once(runner_cmd)
    audit_result = None
    audit_cmd = None
    if runner_result["returncode"] == 0:
        audit_cmd = docker_base() + ["-v", f"{source_mount}:/src:ro", "-v", f"{training_mount}:/evidence:ro",
                                     "-v", f"{audit_out}:/audit:rw", "--entrypoint", "python", IMAGE,
                                     "/src/audit.py", "--evidence", "/evidence", "--freeze", "/src/FREEZE.json",
                                     "--source-root", "/src", "--output", "/audit"]
        audit_result = run_once(audit_cmd)
    report = {"schema": "confidence-trajectory-formal-orchestration-v1",
              "allocation": freeze["allocation"], "issue": 4588,
              "formal_orchestrations": 1, "retries": 0, "tuning": 0,
              "image": IMAGE, "image_id": IMAGE_ID, "freeze_sha256": sha(freeze_raw),
              "source_sha256": freeze["source_sha256"],
              "runner": runner_result, "runner_command": runner_cmd,
              "auditor": audit_result, "auditor_command": audit_cmd,
              "status": "STOP_RUNNER" if runner_result["returncode"] else
                        ("STOP_AUDITOR" if audit_result is None or audit_result["returncode"] else "COMPLETED"),
              "created_unix_ns": time.time_ns()}
    (root / "FORMAL_ORCHESTRATION.json").write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "runner_rc": runner_result["returncode"],
                      "auditor_rc": None if audit_result is None else audit_result["returncode"],
                      "out": str(root)}, sort_keys=True))
    raise SystemExit(0 if report["status"] == "COMPLETED" else 1)


if __name__ == "__main__":
    main()


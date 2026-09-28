"""Fail-closed host preflight and one-shot Docker Desktop orchestration."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

EXP = Path(__file__).resolve().parent
IMAGE = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
CONTAINER_OPTS = [
    "--rm", "--pull=never", "--platform", "linux/amd64", "--network", "none",
    "--read-only", "--cpus", "0.5", "--memory", "256m", "--pids-limit", "32",
    "--shm-size", "32m", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
    "--tmpfs", "/scratch:rw,nosuid,size=32m",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(argv, text=True, encoding="utf-8", errors="replace",
                          capture_output=True, timeout=timeout, check=False)


def docker(argv: list[str], timeout: int = 20) -> subprocess.CompletedProcess:
    return run(["docker", "--context", "desktop-linux", *argv], timeout=timeout)


def preflight(output: Path) -> dict:
    if not output.is_absolute() or output.exists() or not output.parent.is_dir():
        raise RuntimeError("output must be an absolute fresh path under an existing parent")
    freeze = json.loads((EXP / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("schema") != "needle-publication-overlap-freeze-v1":
        raise RuntimeError("freeze schema mismatch")
    if freeze.get("allocation") != "needle-cross-process-publication-overlap-5066-v4-20260928-01":
        raise RuntimeError("allocation mismatch")
    seed = base64.b64decode((EXP / "seed_skill.json.b64").read_bytes().strip(), validate=True)
    if hashlib.sha256(seed).hexdigest() != freeze["input"]["sha256"]:
        raise RuntimeError("input SHA-256 mismatch")
    blob = hashlib.sha1(b"blob " + str(len(seed)).encode("ascii") + b"\0" + seed).hexdigest()
    if blob != freeze["input"]["git_blob"]:
        raise RuntimeError("input Git blob mismatch")
    checks = {}
    for relative, expected in freeze["source_sha256"].items():
        path = EXP / relative
        actual = digest(path)
        checks[relative] = {"expected": expected, "actual": actual, "matches": expected == actual}
        if actual != expected:
            raise RuntimeError("frozen source mismatch: " + relative)
    context = run(["docker", "context", "show"])
    if context.returncode != 0 or context.stdout.strip() != "desktop-linux":
        raise RuntimeError("Docker context is not desktop-linux")
    image = docker(["image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"])
    if image.returncode != 0 or image.stdout.strip() != IMAGE + " linux/amd64":
        raise RuntimeError("pinned image missing or platform mismatch")
    engine = docker(["info", "--format", "{{.ServerVersion}} {{.OSType}}/{{.Architecture}}"], timeout=30)
    if engine.returncode != 0:
        raise RuntimeError("Docker Desktop engine identity unavailable")
    inventory = docker(["ps", "--filter", "status=running", "--format", "{{.ID}} {{.Names}}"])
    if inventory.returncode != 0:
        raise RuntimeError("Docker running-container inventory failed")
    running = [line for line in inventory.stdout.splitlines() if line.strip()]
    return {
        "source_checks": checks,
        "input_sha256": hashlib.sha256(seed).hexdigest(),
        "input_git_blob": blob,
        "docker_context": context.stdout.strip(),
        "docker_invocation_context": "desktop-linux",
        "docker_engine": engine.stdout.strip(),
        "docker_version_image": image.stdout.strip(),
        "running_containers": running,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="absolute path to a fresh output directory")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    checks = preflight(output)
    if args.preflight_only:
        print(json.dumps({"preflight": "PASS_STATIC", "output_created": False,
                          "docker_run_invocations": 0, **checks}, sort_keys=True))
        return 0
    if checks["running_containers"]:
        raise RuntimeError("STOP_SHARED_DOCKER_LOAD: running containers present; do not start")
    output.mkdir(parents=True, exist_ok=False)
    source_mount = f"type=bind,source={EXP},target=/src,readonly"
    output_mount = f"type=bind,source={output},target=/out"
    common = [
        "docker", "--context", "desktop-linux", "run", *CONTAINER_OPTS,
        "--mount", source_mount, "--mount", output_mount,
        "-e", f"FROZEN_IMAGE_ID={IMAGE}", IMAGE,
    ]
    runner_command = common + ["python", "/src/runner.py"]
    auditor_command = common + ["python", "/src/audit.py"]
    started_ns = time.monotonic_ns()
    runner = run(runner_command, timeout=300)
    (output / "runner.stdout.txt").write_text(runner.stdout, encoding="utf-8")
    (output / "runner.stderr.txt").write_text(runner.stderr, encoding="utf-8")
    auditor = None
    if (output / "raw.json").is_file():
        auditor = run(auditor_command, timeout=180)
        (output / "auditor.stdout.txt").write_text(auditor.stdout, encoding="utf-8")
        (output / "auditor.stderr.txt").write_text(auditor.stderr, encoding="utf-8")
    execution = {
        "allocation": "needle-cross-process-publication-overlap-5066-v4-20260928-01",
        "issue": 5082,
        "formal_orchestrations": 1,
        "runner_command": runner_command,
        "runner_exit": runner.returncode,
        "auditor_command": auditor_command if auditor is not None else None,
        "auditor_exit": None if auditor is None else auditor.returncode,
        "docker_context": checks["docker_context"],
        "docker_engine": checks["docker_engine"],
        "image_identity": checks["docker_version_image"],
        "source_sha256_checks": checks["source_checks"],
        "running_containers_before": checks["running_containers"],
        "started_ns": started_ns,
        "finished_ns": time.monotonic_ns(),
        "disposition": "AUDIT_REQUIRED" if auditor is None else
            ("AUDIT_EXIT_ZERO" if auditor.returncode == 0 else "FAIL_AUDIT"),
    }
    (output / "execution.json").write_text(json.dumps(execution, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest = {}
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            manifest[str(path.relative_to(output)).replace("\\", "/")] = {
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runner_exit": runner.returncode,
                      "auditor_exit": None if auditor is None else auditor.returncode,
                      "output": str(output), "files": len(manifest)}, sort_keys=True))
    return 0 if auditor is not None and auditor.returncode == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"preflight_orchestration_error": type(exc).__name__,
                          "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise

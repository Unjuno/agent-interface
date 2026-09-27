"""Host-side fail-closed preflight and one-shot local Docker orchestration."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

EXP = Path(__file__).resolve().parent
REPO = EXP.parents[2]
IMAGE = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
EXPECTED_SEED = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"
CONTAINER_EXP = "/src/research/system1/needle_cross_process_publication_5045_v1"
SEED = REPO / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, text=True, encoding="utf-8", errors="replace", capture_output=True)


def frozen_input_sha(freeze: dict) -> str:
    try:
        value = freeze["input"]["sha256"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("freeze must store the input digest at input.sha256") from exc
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise RuntimeError("freeze input.sha256 must be 64 lowercase hexadecimal characters")
    return value


def validate_freeze_identity(freeze: dict, seed_sha: str) -> None:
    if freeze.get("schema") != "needle-cross-process-publication-freeze-v1":
        raise RuntimeError("freeze schema mismatch")
    if freeze.get("image_id") != IMAGE:
        raise RuntimeError("freeze image identity mismatch")
    if frozen_input_sha(freeze) != seed_sha:
        raise RuntimeError("freeze input SHA-256 mismatch")


def validate_sources(exp: Path, source_hashes: dict) -> dict:
    results = {}
    for relative, expected in source_hashes.items():
        path = exp / relative
        actual = digest(path)
        results[relative] = {"expected": expected, "actual": actual, "matches": expected == actual}
        if actual != expected:
            raise RuntimeError(f"frozen source mismatch: {relative}")
    return results


def validate_output_path(output: Path) -> None:
    if not output.is_absolute() or output.exists():
        raise RuntimeError("formal output path must be absolute and not exist before invocation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="absolute path to a new, empty output directory")
    parser.add_argument("--preflight-only", action="store_true", help="validate frozen inputs and sources without Docker or output creation")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    validate_output_path(output)
    if digest(SEED) != EXPECTED_SEED:
        raise RuntimeError("exact seed-3788 skill.json SHA-256 mismatch")
    freeze = json.loads((EXP / "FREEZE.json").read_text(encoding="utf-8"))
    validate_freeze_identity(freeze, EXPECTED_SEED)
    source_results = validate_sources(EXP, freeze["source_sha256"])
    if args.preflight_only:
        print(json.dumps({"preflight": "PASS_STATIC", "output_created": False, "docker_invocations": 0}, sort_keys=True))
        return 0
    if run(["docker", "context", "show"]).stdout.strip() != "desktop-linux":
        raise RuntimeError("Docker context is not desktop-linux")
    image = run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"])
    if image.returncode != 0 or image.stdout.strip() != IMAGE + " linux/amd64":
        raise RuntimeError("pinned image is unavailable or has a platform mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    limits = [
        "--rm", "--pull=never", "--platform", "linux/amd64", "--network", "none",
        "--read-only", "--cpus", "0.25", "--memory", "256m", "--pids-limit", "32",
        "--shm-size", "32m", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--mount", f"type=bind,source={REPO},target=/src,readonly",
        "--mount", f"type=bind,source={output},target=/out",
        "-e", f"FROZEN_IMAGE_ID={IMAGE}",
    ]
    runner_command = ["docker", "run", *limits, IMAGE, "python", CONTAINER_EXP + "/runner.py"]
    auditor_command = ["docker", "run", *limits, IMAGE, "python", CONTAINER_EXP + "/audit.py"]
    started = time.time_ns()
    runner = run(runner_command)
    (output / "runner.stdout.txt").write_text(runner.stdout, encoding="utf-8")
    (output / "runner.stderr.txt").write_text(runner.stderr, encoding="utf-8")
    auditor = None
    if runner.returncode == 0 and (output / "raw.json").is_file():
        auditor = run(auditor_command)
        (output / "auditor.stdout.txt").write_text(auditor.stdout, encoding="utf-8")
        (output / "auditor.stderr.txt").write_text(auditor.stderr, encoding="utf-8")
    execution = {
        "allocation": "needle-cross-process-publication-5045-v1",
        "issue": 5045,
        "formal_orchestrations": 1,
        "runner_command": runner_command,
        "runner_exit": runner.returncode,
        "auditor_command": auditor_command if auditor is not None else None,
        "auditor_exit": auditor.returncode if auditor is not None else None,
        "image_identity": image.stdout.strip(),
        "source_sha256_checks": source_results,
        "input_sha256": digest(SEED),
        "host_platform": platform.platform(),
        "docker_context": "desktop-linux",
        "started_unix_ns": started,
        "finished_unix_ns": time.time_ns(),
        "disposition": "AUDIT_REQUIRED" if auditor is None else ("AUDIT_EXIT_ZERO" if auditor.returncode == 0 else "FAIL_AUDIT"),
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
    print(json.dumps({"runner_exit": runner.returncode, "auditor_exit": None if auditor is None else auditor.returncode,
                      "output": str(output), "files": len(manifest)}, sort_keys=True))
    return 0 if auditor is not None and auditor.returncode == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        print(json.dumps({"formal_preflight_orchestration_error": type(exc).__name__, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise



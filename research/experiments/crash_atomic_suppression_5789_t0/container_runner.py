"""Bounded Docker/Obstac launcher; formal mode requires an allocated context."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


IMAGE = "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
BASE = Path(__file__).parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_freeze() -> tuple[dict[str, object], str]:
    path = BASE / "FREEZE.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"STOP_FREEZE_MANIFEST:{exc}") from exc
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if data.get("image_ref") != IMAGE:
        raise SystemExit("STOP_IMAGE_REFERENCE_NOT_PINNED")
    if data.get("source_sha256") != {
        name: sha256(BASE / name) for name in ("protocol.py", "worker.py", "runner.py", "audit.py")
    }:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    if data.get("audit_sha256") != sha256(BASE / "audit.py"):
        raise SystemExit("STOP_AUDIT_HASH_MISMATCH")
    if data.get("schedule_sha256") != schedule_sha256():
        raise SystemExit("STOP_SCHEDULE_HASH_MISMATCH")
    return data, digest


def schedule_sha256() -> str:
    from protocol import schedule_sha256 as calculate

    return calculate()


def docker_command(
    *, docker: str, context: str, platform: str, source: Path, output: Path,
    runtime: dict[str, str], freeze_digest: str, mode: str,
    include_manifest: bool = False,
    script: str = "/work/source/runner.py", arguments: tuple[str, ...] = ("--out", "/work/out"),
) -> list[str]:
    environment = ["-e", f"OBSTAC_RUN_KIND={mode}", "-e", f"OBSTAC_DOCKER_CONTEXT={context}",
        "-e", f"OBSTAC_PLATFORM={platform}", "-e", f"OBSTAC_SOURCE_COMMIT={runtime['source_commit']}",
        "-e", f"OBSTAC_IMAGE_ID={runtime['image_id']}", "-e", f"OBSTAC_FREEZE_SHA256={freeze_digest}"]
    if include_manifest:
        environment.extend(["-e", f"OBSTAC_DOCKER_HOST={runtime['docker_host']}",
                            "-e", f"OBSTAC_AUDIT_SHA256={sha256(BASE / 'audit.py')}"])
    command = [docker, "--context", context, "run", "--rm", "--platform", platform,
        "--network", "none", "--read-only", "--cpus", "1", "--memory", "256m",
        "--pids-limit", "64", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "--mount", f"type=bind,src={source.resolve()},dst=/work/source,readonly",
        "--mount", f"type=bind,src={output.resolve()},dst=/work/out",
        *environment,
        IMAGE, "python", "-B", script, *arguments]
    return command


def run_candidate(*, docker: str, context: str, platform: str, output: Path,
                  runtime: dict[str, str], digest: str, mode: str, endpoint: str,
                  source_commit: str) -> int:
    command = docker_command(docker=docker, context=context, platform=platform,
        source=BASE, output=output, runtime={**runtime, "source_commit": source_commit},
        freeze_digest=digest, mode=mode,
        include_manifest=True)
    command[2:2] = ["--host", endpoint]
    return subprocess.run(command, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("construction", "formal"), required=True)
    parser.add_argument("--candidate-out", type=Path, required=True)
    parser.add_argument("--audit-out", type=Path)
    parser.add_argument("--audit-raw", type=Path)
    parser.add_argument("--docker", default="docker")
    args = parser.parse_args()
    if args.mode == "formal" and os.environ.get("OBSTAC_RUN_KIND") != "formal":
        raise SystemExit("STOP_NO_FORMAL_ALLOCATION")
    mode = args.mode
    if mode == "construction":
        context = os.environ.get("OBSTAC_CONSTRUCTION_CONTEXT", "")
        endpoint = os.environ.get("OBSTAC_CONSTRUCTION_DOCKER_HOST", "")
        if not context or not endpoint:
            raise SystemExit("STOP_CONSTRUCTION_ENDPOINT_MISSING")
        runtime = {
            "source_commit": "construction-only",
            "image_id": "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
            "docker_host": endpoint,
        }
        args.candidate_out.mkdir(parents=True, exist_ok=True)
        if any(args.candidate_out.iterdir()):
            raise SystemExit("STOP_NONEMPTY_OUTPUT")
        source_hash = hashlib.sha256((BASE / "container_runner.py").read_bytes()).hexdigest()
        env = {
            "OBSTAC_RUN_KIND": "construction",
            "OBSTAC_DOCKER_CONTEXT": context,
            "OBSTAC_DOCKER_HOST": endpoint,
            "OBSTAC_PLATFORM": "linux/arm64",
            "OBSTAC_SOURCE_COMMIT": "construction-only",
            "OBSTAC_IMAGE_ID": runtime["image_id"],
            "OBSTAC_FREEZE_SHA256": "construction-only",
            "OBSTAC_AUDIT_SHA256": sha256(BASE / "audit.py"),
        }
        os.environ.update(env)
        command = docker_command(docker=args.docker, context=context, platform="linux/arm64",
            source=BASE, output=args.candidate_out, runtime=runtime, freeze_digest="construction-only",
            mode=mode, include_manifest=True, arguments=("--out", "/work/out", "--construction"))
        command[2:2] = ["--host", endpoint]
        return subprocess.run(command, check=False).returncode

    frozen, digest = load_freeze()
    runtime = frozen.get("runtime")
    if not isinstance(runtime, dict):
        raise SystemExit("STOP_RUNTIME_MANIFEST")
    if mode == "formal":
        context = os.environ.get("OBSTAC_DOCKER_CONTEXT", "")
        endpoint = os.environ.get("OBSTAC_DOCKER_HOST", "")
        if not context or not endpoint:
            raise SystemExit("STOP_ASSIGNED_ENDPOINT_MISSING")
        if context != runtime.get("docker_context") or endpoint != runtime.get("docker_host"):
            raise SystemExit("STOP_ASSIGNED_ENDPOINT_MISMATCH")
        if os.environ.get("OBSTAC_AUDIT_SHA256") != frozen.get("audit_sha256"):
            raise SystemExit("STOP_ASSIGNED_AUDIT_HASH_MISMATCH")
        if os.environ.get("OBSTAC_FREEZE_SHA256") != digest:
            raise SystemExit("STOP_ASSIGNED_FREEZE_DIGEST_MISMATCH")
        if os.environ.get("OBSTAC_SOURCE_COMMIT") != runtime.get("source_commit"):
            raise SystemExit("STOP_ASSIGNED_SOURCE_COMMIT_MISMATCH")
        if os.environ.get("OBSTAC_IMAGE_ID") != runtime.get("image_id"):
            raise SystemExit("STOP_ASSIGNED_IMAGE_ID_MISMATCH")
        if os.environ.get("OBSTAC_PLATFORM") != runtime.get("platform"):
            raise SystemExit("STOP_ASSIGNED_PLATFORM_MISMATCH")
        if args.audit_out is None or args.audit_raw is None:
            raise SystemExit("STOP_AUDIT_PATHS_REQUIRED")
        for path in (args.candidate_out, args.audit_out):
            if path.exists() and any(path.iterdir()):
                raise SystemExit("STOP_NONEMPTY_OUTPUT")
            path.mkdir(parents=True, exist_ok=True)
        if args.candidate_out.resolve() == args.audit_out.resolve():
            raise SystemExit("STOP_OUTPUT_MOUNTS_NOT_SEPARATE")
    context = str(context)
    platform = "linux/arm64"
    frozen_runtime = frozen.get("runtime")
    if not isinstance(frozen_runtime, dict):
        raise SystemExit("STOP_RUNTIME_MANIFEST")
    if mode == "formal" and runtime != frozen_runtime:
        raise SystemExit("STOP_ASSIGNED_RUNTIME_DIFFERS_FROM_FREEZE")
    environment = {
        "OBSTAC_RUN_KIND": mode,
        "OBSTAC_DOCKER_CONTEXT": context,
        "OBSTAC_DOCKER_HOST": endpoint,
        "OBSTAC_AUDIT_SHA256": str(frozen["audit_sha256"]),
    }
    os.environ.update(environment)
    exit_code = run_candidate(docker=args.docker, context=context, platform=platform,
        output=args.candidate_out, runtime=runtime, digest=digest, mode=mode, endpoint=endpoint,
        source_commit=str(runtime["source_commit"]))
    if exit_code != 0 or mode != "formal":
        return exit_code
    raw = args.audit_raw.resolve()
    expected_raw = (args.candidate_out / "raw.jsonl").resolve()
    if raw != expected_raw or not raw.is_file():
        raise SystemExit("STOP_RAW_PATH_MISMATCH_OR_MISSING")
    audit_command = docker_command(
        docker=args.docker,
        context=context,
        platform=platform,
        source=BASE,
        output=args.audit_out,
        runtime=runtime,
        freeze_digest=digest,
        mode="formal",
        include_manifest=True,
        script="/work/source/audit.py",
        arguments=("--raw", "/work/raw.jsonl", "--out", "/work/out/audit.json"),
    )
    source_mount = f"type=bind,src={BASE.resolve()},dst=/work/source,readonly"
    output_mount = f"type=bind,src={args.audit_out.resolve()},dst=/work/out"
    audit_command = [arg for arg in audit_command if arg not in (source_mount, output_mount)]
    mount_index = audit_command.index("--network")
    audit_command[mount_index:mount_index] = [
        "--mount", source_mount,
        "--mount", output_mount,
        "--mount", f"type=bind,src={raw},dst=/work/raw.jsonl,readonly",
    ]
    audit_command[2:2] = ["--host", endpoint]
    return subprocess.run(audit_command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

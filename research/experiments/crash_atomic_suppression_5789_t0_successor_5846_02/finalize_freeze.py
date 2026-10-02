"""Finalize allocation-02 runtime identity and checksums before candidate launch."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import container_runner


HASHED_FILES = (
    "FREEZE.json", "FREEZE.md", "protocol.py", "worker.py", "runner.py", "audit.py",
    "container_runner.py", "finalize_freeze.py", "test_protocol.py", "test_execution.py",
    "README.md", "CONSTRUCTION.md",
)
SOURCE_FILES = ("protocol.py", "worker.py", "runner.py", "audit.py")
GUEST_CANDIDATE = Path("/study/results/5846-02/candidate")
GUEST_AUDIT = Path("/study/results/5846-02/audit")
GUEST_RAW = GUEST_CANDIDATE / "raw.jsonl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_digest(manifest: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(
        manifest, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def finalize_manifest(
    manifest: dict[str, object], *, base: Path, host_source_root: Path,
    source_commit: str, image_id: str, docker_context: str, docker_host: str,
) -> dict[str, object]:
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise SystemExit("STOP_SOURCE_COMMIT_SCHEMA")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise SystemExit("STOP_IMAGE_ID_SCHEMA")
    if docker_context != "crash-atomic-5846-local-02":
        raise SystemExit("STOP_DOCKER_CONTEXT_NOT_ASSIGNED")
    if docker_host != "unix:///var/run/docker.sock":
        raise SystemExit("STOP_DOCKER_ENDPOINT_NOT_ASSIGNED")
    if not host_source_root.is_absolute():
        raise SystemExit("STOP_HOST_SOURCE_ROOT_NOT_ABSOLUTE")

    result = json.loads(json.dumps(manifest))
    runtime = result.get("runtime")
    if not isinstance(runtime, dict):
        raise SystemExit("STOP_RUNTIME_MANIFEST")
    runtime.update({
        "source_commit": source_commit,
        "image_id": image_id,
        "docker_context": docker_context,
        "docker_host": docker_host,
        "host_source_root": str(host_source_root),
    })
    result["source_sha256"] = {name: sha256(base / name) for name in SOURCE_FILES}
    result["audit_sha256"] = sha256(base / "audit.py")
    result["launcher_sha256"] = sha256(base / "container_runner.py")
    result["schedule_sha256"] = container_runner.schedule_sha256()

    guest_args = argparse.Namespace(
        mode="formal", candidate_out=GUEST_CANDIDATE,
        audit_out=GUEST_AUDIT, audit_raw=GUEST_RAW, docker="docker",
    )
    host_args = argparse.Namespace(
        mode="formal",
        candidate_out=container_runner.guest_path(GUEST_CANDIDATE, host_source_root).resolve(),
        audit_out=container_runner.guest_path(GUEST_AUDIT, host_source_root).resolve(),
        audit_raw=container_runner.guest_path(GUEST_RAW, host_source_root).resolve(),
        docker="docker",
    )
    result["formal_argv"] = container_runner.invocation_argv(host_args)
    return result


def write_checksums(base: Path) -> None:
    rows = [f"{sha256(base / name)}  {name}" for name in HASHED_FILES]
    (base / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--host-source-root", type=Path, required=True)
    parser.add_argument("--docker-context", required=True)
    parser.add_argument("--docker-host", required=True)
    args = parser.parse_args()
    freeze_path = Path(__file__).with_name("FREEZE.json")
    try:
        current = json.loads(freeze_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"STOP_FREEZE_MANIFEST:{exc}") from exc
    if args.docker_context != "crash-atomic-5846-local-02":
        raise SystemExit("STOP_DOCKER_CONTEXT_NOT_ASSIGNED")
    if args.docker_host != "unix:///var/run/docker.sock":
        raise SystemExit("STOP_DOCKER_ENDPOINT_NOT_ASSIGNED")
    container_runner.verify_context_endpoint(
        docker="docker", context=args.docker_context, endpoint=args.docker_host,
    )
    observed = container_runner.verify_image_identity(
        docker="docker", context=args.docker_context, platform="linux/arm64",
        expected_image_id=args.image_id,
    )
    if observed["image_id"] != args.image_id:
        raise SystemExit("STOP_FINALIZER_IMAGE_ID_CHANGED")
    updated = finalize_manifest(
        current, base=Path(__file__).parent, host_source_root=args.host_source_root,
        source_commit=args.source_commit, image_id=args.image_id,
        docker_context=args.docker_context, docker_host=args.docker_host,
    )
    freeze_path.write_text(json.dumps(updated, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    write_checksums(Path(__file__).parent)
    print(json.dumps({
        "freeze_sha256": manifest_digest(updated),
        "source_commit": args.source_commit,
        "image_id": args.image_id,
        "formal_argv": updated["formal_argv"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Verify the frozen Issue #3814 source/image gate before the single runner call."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import os
import sys


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(source: Path, image_ref: str, image_id: str, container_platform: str) -> dict:
    freeze = json.loads((source / "research/issue_3814_jsonl_framing_v1/FREEZE.json").read_text(encoding="utf-8"))
    mismatches = []
    source_checks = {}
    for relative, expected in freeze["source_sha256"].items():
        path = source / relative
        actual = sha(path.read_bytes()) if path.is_file() else None
        source_checks[relative] = actual == expected
        if actual != expected:
            mismatches.append("SOURCE_SHA256:" + relative)
    expected_image = freeze["C"]["image"]
    expected_id = freeze["C"]["image_id"]
    expected_platform = freeze["C"]["platform"]
    docker_server = os.environ.get("ISSUE3814_DOCKER_SERVER")
    if image_ref != expected_image:
        mismatches.append("IMAGE_REF_MISMATCH")
    if image_id != expected_id:
        mismatches.append("IMAGE_ID_MISMATCH")
    if container_platform != expected_platform:
        mismatches.append("PLATFORM_MISMATCH")
    if docker_server != freeze["C"]["docker_server"]:
        mismatches.append("DOCKER_SERVER_MISMATCH")
    if platform.machine().lower() not in ("x86_64", "amd64"):
        mismatches.append("CONTAINER_ARCH_MISMATCH")
    if sys.version_info[:2] != (3, 12):
        mismatches.append("PYTHON_VERSION_MISMATCH")
    if freeze["formal"]["invocations"] != 0 or freeze["formal"]["maximum"] != 1:
        mismatches.append("ALLOCATION_COUNT_INVALID")
    return {
        "schema": "issue-3814-source-image-preflight-v1",
        "disposition": "PASS_SOURCE_FREEZE" if not mismatches else "STOP_SOURCE_OR_IMAGE_MISMATCH",
        "source_checks": source_checks,
        "source_check_count": len(source_checks),
        "image_ref": image_ref,
        "image_id": image_id,
        "platform": container_platform,
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "docker_server": docker_server,
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--image-ref", required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--run-output", type=Path)
    args = parser.parse_args()
    result = verify(args.source, args.image_ref, args.image_id, args.platform)
    print(json.dumps(result, sort_keys=True, indent=2))
    if result["mismatches"]:
        return 20
    if args.check_only:
        return 0
    if args.run_output is None:
        parser.error("--run-output is required unless --check-only is set")
    # Import the formal runner only after every frozen source and environment gate passes.
    sys.path.insert(0, str(args.source))
    from research.issue_3814_jsonl_framing_v1.runner import run
    run(args.run_output, args.source, preflight=result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

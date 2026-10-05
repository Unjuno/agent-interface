"""Additive v2 engineering audit; original T0A verdict is not changed."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class AuditError(ValueError):
    pass


EXPECTED_FILES = {
    "Dockerfile": (336, "ec8ab4d198d4a6cfc163e9cbd4098c7d68b86f0fa14f870fa5d8addee310352d"),
    "payload.txt": (36, "3280e32e693397e74af56b9f9f0dd473dd663224a3c62883b33cbc8828d7c383"),
    "probe.py": (819, "78a615ffacc99f453c7f81995db92d962ec0ec60069ebc3415d0a89ddcc20893"),
    'build.output.txt': (511, 'a76aa6cbfdd50dd50c647e6c582c4577115298ea1a2c102fa63bf7df84e37b4d'),
    'run.output.txt': (350, '207e6eb72a3e616cca690fb8bb7477bef4139923224690bf49490285efcde227'),
    'POSTRUN_CHECK.json': (491, '9e512438029a0da95f88fc5078c7fca730ddc03d0eea90d39cadced8588c563f'),
    'RUN.json': (2188, '518bc8c0a831d1dbc5443459d520167cd51f98241f5d3a1067c80674671fba88'),
}
BASE_DIGEST = "f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
IMAGE_TAG = "agent-interface/wslc-build-smoke:20261003t0"
CONTAINER_NAME = "agent-interface-wslc-build-smoke-t0-20261003"
IMAGE_ID = "sha256:1c325ff52bc0515d073900c048fd1707f2beec00cfdb892ac88ded2defc1a716"
PAYLOAD_SHA256 = "3280e32e693397e74af56b9f9f0dd473dd663224a3c62883b33cbc8828d7c383"
WARNING = (
    "wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. "
    "Memory limited without swap."
)


def read_json(root: Path, name: str) -> dict[str, Any]:
    try:
        value = json.loads((root / name).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"invalid or missing {name}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{name} must contain a JSON object")
    return value


def read_text(root: Path, name: str) -> str:
    try:
        return (root / name).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AuditError(f"invalid or missing {name}") from exc


def audit(root: Path) -> dict[str, Any]:
    for name, (expected_bytes, expected_sha) in EXPECTED_FILES.items():
        try:
            data = (root / name).read_bytes()
        except OSError as exc:
            raise AuditError(f"missing frozen source: {name}") from exc
        if len(data) != expected_bytes or hashlib.sha256(data).hexdigest() != expected_sha:
            raise AuditError(f"frozen source mismatch: {name}")

    dockerfile = read_text(root, "Dockerfile")
    if f"FROM python@sha256:{BASE_DIGEST}" not in dockerfile or "RUN " in dockerfile:
        raise AuditError("Dockerfile base or no-RUN gate mismatch")

    build = read_text(root, "build.output.txt")
    if "[1/4] CACHED\n" not in build or f"FROM docker.io/library/python@sha256:{BASE_DIGEST}" not in build:
        raise AuditError("build output lacks pinned cached base evidence")
    if f"writing image {IMAGE_ID}" not in build or f"naming to docker.io/{IMAGE_TAG}" not in build:
        raise AuditError("build output image identity mismatch")

    output_lines = read_text(root, "run.output.txt").splitlines()
    if len(output_lines) != 2 or output_lines[0] != WARNING:
        raise AuditError("run output warning or line count mismatch")
    try:
        receipt = json.loads(output_lines[1])
    except json.JSONDecodeError as exc:
        raise AuditError("run stdout is not valid JSON") from exc
    if receipt != {
        "payload_bytes": 36,
        "payload_sha256": PAYLOAD_SHA256,
        "platform": "Linux",
        "python": "3.12.14",
        "schema": "wslc-dockerfile-build-smoke-v1",
        "status": "PASS_WSLc_DOCKERFILE_BUILD_RUN_SMOKE",
    }:
        raise AuditError("run stdout receipt differs from the frozen expected result")

    post = read_json(root, "POSTRUN_CHECK.json")
    if post.get("both_exit_code") != 0 or post.get("image_tag_found") != IMAGE_TAG:
        raise AuditError("post-run image inventory mismatch")
    if post.get("image_id") != IMAGE_ID or post.get("target_container_name") != CONTAINER_NAME:
        raise AuditError("post-run image/container identity mismatch")
    if post.get("target_container_present_after_run") is not False:
        raise AuditError("named container remains after run")

    run = read_json(root, "RUN.json")
    build_record, run_record = run.get("build", {}), run.get("run", {})
    if run.get("status") != "PASS_WSLc_DOCKERFILE_BUILD_RUN_SMOKE":
        raise AuditError("RUN status mismatch")
    if build_record.get("exit_code") != 0 or build_record.get("invocations") != 1 or build_record.get("retries") != 0:
        raise AuditError("build count or exit mismatch")
    if run_record.get("exit_code") != 0 or run_record.get("invocations") != 1 or run_record.get("retries") != 0:
        raise AuditError("run count or exit mismatch")
    if run_record.get("payload_sha256") != PAYLOAD_SHA256 or run_record.get("container_removed_by_rm") is not True:
        raise AuditError("RUN receipt mismatch")
    if run.get("scope", {}).get("docker_runs") != 0 or run.get("scope", {}).get("retries") != 0:
        raise AuditError("scope count mismatch")
    if run.get("scope", {}).get("memory_limit_effectiveness_claimed") is not False:
        raise AuditError("unsupported memory-cap claim present")

    if build_record.get("result_image_id") != IMAGE_ID:
        raise AuditError("RUN build image identity mismatch")
    if run.get("postrun_check", {}).get("image_id") != IMAGE_ID:
        raise AuditError("RUN postrun image identity mismatch")

    return {
        "status": "PASS_RETAINED_RECEIPT_V2_ENGINEERING",
        "frozen_inputs_checked": len(EXPECTED_FILES),
        "wslc_builds": 1,
        "wslc_runs": 1,
        "retries": 0,
        "payload_sha256": PAYLOAD_SHA256,
        "image_id": IMAGE_ID,
        "target_container_present_after_run": False,
        "memory_limit_effectiveness_claimed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.root)
    except AuditError as exc:
        print(json.dumps({"status": "STOP_RETAINED_RECEIPT_V2_INVALID", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

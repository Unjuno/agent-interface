#!/usr/bin/env python3
"""Independent host-side audit of the WSLc construction-only receipt."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


IMAGE_ID = "sha256:048a0de5d4322054f9d92a9dfd36f4cab1cd82dfbd1042ce2c51bd94f7e45d32"
IMAGE_DIGEST = "pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067"
PROBE = b"WSLc unprivileged output bind writable\n"


def audit(root: Path) -> dict:
    errors: list[str] = []
    if (root / "exit_code.txt").read_text(encoding="ascii").strip() != "0":
        errors.append("construction container exit code was not zero")
    stdout = (root / "stdout.txt").read_text(encoding="utf-8")
    stderr = (root / "stderr.txt").read_text(encoding="utf-8")
    if "construction_tests=10 output_probe=PASS" not in stdout:
        errors.append("construction summary missing")
    passed = re.findall(r"^test_[A-Za-z0-9_]+ \(.*\) \.\.\. ok$", stderr, re.MULTILINE)
    if len(passed) != 10 or "Ran 10 tests" not in stderr or not re.search(r"^OK$", stderr, re.MULTILINE):
        errors.append(f"expected 10 passing test receipts, got {len(passed)}")
    if (root / "write_probe.txt").read_bytes() != PROBE:
        errors.append("unprivileged writable-bind probe bytes differ")
    if (root / "containers_after.txt").read_text(encoding="ascii").strip():
        errors.append("post-run WSLc inventory is not empty")
    inspected = json.loads((root / "image_inspect.json").read_text(encoding="utf-8"))
    if not isinstance(inspected, list) or len(inspected) != 1:
        errors.append("image inspect did not return exactly one object")
    else:
        image = inspected[0]
        if image.get("Id") != IMAGE_ID or image.get("Os") != "linux" or image.get("Architecture") != "amd64":
            errors.append("cached image ID/platform mismatch")
        if IMAGE_DIGEST not in image.get("RepoDigests", []):
            errors.append("pinned registry digest absent from image inspect")
    inventory = (root / "images_digests.txt").read_text(encoding="utf-8")
    digest_token = IMAGE_DIGEST.split("@", 1)[1]
    if digest_token not in inventory or IMAGE_ID not in inventory:
        errors.append("pinned image digest/ID absent from local image inventory")
    return {
        "result": "PASS_WSLc_CONSTRUCTION_PREFLIGHT_SCOPED" if not errors else "FAIL_PREFLIGHT_RECEIPT",
        "checks": {
            "container_exit_zero": not any("exit code" in error for error in errors),
            "ten_tests_passed": len(passed) == 10,
            "unprivileged_output_bind_exact_bytes": (root / "write_probe.txt").read_bytes() == PROBE,
            "container_removed": not (root / "containers_after.txt").read_text(encoding="ascii").strip(),
            "pinned_image_identity": not any("image" in error for error in errors),
            "cgroup_swap_warning_retained": "does not support swap limit capabilities" in stderr,
        },
        "caveat": "Construction/runtime evidence only; no CUDA candidate, GPU worker, or scientific result.",
        "errors": errors,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_preflight.py EVIDENCE_DIR")
    result = audit(Path(sys.argv[1]))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["result"].startswith("PASS_") else 1)

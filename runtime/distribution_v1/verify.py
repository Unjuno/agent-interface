"""Verify deterministic standalone doctor artifact and source closure."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from .build import FIXED_TIME, GENERATED, SOURCE_FILES, _source_bytes


def verify(root: Path, artifact: Path, manifest_path: Path, expected_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    raw = artifact.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    errors = []
    if digest != manifest["sha256"]:
        errors.append("artifact_manifest_sha")
    if digest != expected["sha256"]:
        errors.append("artifact_expected_sha")
    if len(raw) != manifest["bytes"]:
        errors.append("artifact_size")

    expected_entries = sorted(list(SOURCE_FILES) + list(GENERATED) + ["BUILD.json"])
    with zipfile.ZipFile(artifact, "r") as archive:
        names = archive.namelist()
        if names != expected_entries:
            errors.append("entry_set_or_order")
        for info in archive.infolist():
            if info.date_time != FIXED_TIME:
                errors.append(f"timestamp:{info.filename}")
            if info.compress_type != zipfile.ZIP_STORED:
                errors.append(f"compression:{info.filename}")
        for rel in SOURCE_FILES:
            if archive.read(rel) != _source_bytes(root, rel):
                errors.append(f"source_bytes:{rel}")
        build = json.loads(archive.read("BUILD.json"))
        if build.get("support_claim") is not False or build.get("ready_for_side_effects") is not False:
            errors.append("build_claim")

    result = {"pass": not errors, "sha256": digest, "errors": errors, "entries": len(expected_entries)}
    if errors:
        raise SystemExit("VERIFY_FAIL " + ",".join(errors))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve(), args.artifact, args.manifest, args.expected), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

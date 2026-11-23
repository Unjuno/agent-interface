"""Verify a portable runtime's included source against the frozen main tree."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: verify_main_manifest.py REPO_ROOT MANIFEST MAIN_SHA")
    root = Path(sys.argv[1])
    manifest_path = Path(sys.argv[2])
    main_sha = sys.argv[3]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact = manifest_path.with_name(manifest["artifact"])
    errors: list[str] = []
    archive_bytes = artifact.read_bytes()
    archive_sha = hashlib.sha256(archive_bytes).hexdigest()
    if archive_sha != manifest.get("sha256"):
        errors.append("archive SHA-256 differs from manifest")
    if len(archive_bytes) != manifest.get("bytes"):
        errors.append("archive byte length differs from manifest")

    rows = manifest.get("source_files")
    if not isinstance(rows, list) or not rows:
        errors.append("manifest source_files is missing or empty")
        rows = []
    try:
        with zipfile.ZipFile(artifact) as zf:
            names = set(zf.namelist())
            for row in rows:
                path = row["path"]
                data = subprocess.run(
                    ["git", "show", f"{main_sha}:{path}"], cwd=root,
                    check=True, capture_output=True).stdout
                digest = hashlib.sha256(data).hexdigest()
                if digest != row.get("sha256") or len(data) != row.get("bytes"):
                    errors.append(f"main blob differs from manifest: {path}")
                if path not in names or zf.read(path) != data:
                    errors.append(f"archive payload differs from main blob: {path}")
    except Exception as error:
        errors.append(f"verification error: {type(error).__name__}: {error}")

    print(json.dumps({
        "schema": "agent-interface/win32-main-runtime-manifest-audit-v1",
        "main_sha": main_sha,
        "source_revision": manifest.get("source_revision"),
        "source_files_checked": len(rows),
        "archive_sha256": archive_sha,
        "archive_bytes": len(archive_bytes),
        "passed": not errors,
        "errors": errors,
    }, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

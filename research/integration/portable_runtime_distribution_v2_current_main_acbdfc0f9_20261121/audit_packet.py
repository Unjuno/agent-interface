"""Verify portable runtime bytes against the pinned main source manifest."""

from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
EXPECTED_REVISION = "acbdfc0f9db00358cbb755baebe7c7641867aeda"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    artifact = PACKET / "agent-interface-runtime.pyz"
    manifest = json.loads((PACKET / "manifest.json").read_text(encoding="utf-8"))
    checksums = (PACKET / "sha256.txt").read_text(encoding="utf-8").split()
    assert manifest["source_revision"] == EXPECTED_REVISION
    assert manifest["sha256"] == sha256(artifact.read_bytes())
    assert checksums == [manifest["sha256"], artifact.name]
    with zipfile.ZipFile(artifact) as archive:
        assert archive.testzip() is None
        assert sorted(archive.namelist()) == manifest["entries"]
        build = json.loads(archive.read("BUILD.json"))
        assert build["source_revision"] == EXPECTED_REVISION
        assert build["source_files"] == manifest["source_files"]
    mismatches = []
    for row in manifest["source_files"]:
        content = subprocess.check_output(
            ["git", "show", f"{EXPECTED_REVISION}:{row['path']}"], cwd=ROOT)
        if len(content) != row["bytes"] or sha256(content) != row["sha256"]:
            mismatches.append(row["path"])
    result = {
        "status": "PASS" if not mismatches else "FAIL",
        "source_revision": EXPECTED_REVISION,
        "artifact_bytes": artifact.stat().st_size,
        "artifact_sha256": manifest["sha256"],
        "archive_entries": len(manifest["entries"]),
        "source_files_checked": len(manifest["source_files"]),
        "source_hash_mismatches": mismatches,
    }
    (PACKET / "audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sums_path = PACKET / "SHA256SUMS"
    if sums_path.exists():
        declared = {}
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            expected, relative = line.split("  ", 1)
            declared[relative] = expected
        actual = {
            path.relative_to(PACKET).as_posix(): sha256(path.read_bytes())
            for path in PACKET.rglob("*")
            if path.is_file() and path != sums_path
        }
        if declared != actual:
            raise SystemExit("SHA256SUMS does not exactly cover packet files")
    print(json.dumps(result, sort_keys=True))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

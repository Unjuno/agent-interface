"""Restore retained #5274 evidence; never execute a scientific allocation.

Usage (Python 3.13): python restore.py NEW_OUTPUT_DIRECTORY
The six binary parts and PACK.json must be beside this script.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile

EXPECTED = "7fb949e3fe109494377d1b108212876c4b4d5d703f13758bfb59d3a999b99016"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def restore(root: Path, target: Path) -> dict:
    if target.exists() or target.is_symlink():
        raise ValueError("refusing existing output")
    pack = json.loads((root / "PACK.json").read_text(encoding="utf-8"))
    if pack.get("sha256") != EXPECTED or len(pack.get("parts", [])) != 6:
        raise ValueError("unexpected pack identity")
    chunks = []
    for i, item in enumerate(pack["parts"]):
        name = f"evidence.tar.xz.part{i:02d}"
        if item.get("path") != name:
            raise ValueError("unexpected part order/path")
        data = (root / name).read_bytes()
        if len(data) != item["bytes"] or digest(data) != item["sha256"]:
            raise ValueError(f"part integrity failure: {name}")
        chunks.append(data)
    archive = b"".join(chunks)
    if len(archive) != 68036 or digest(archive) != EXPECTED:
        raise ValueError("archive integrity failure")
    # Validate every member before creating the destination. No links or devices.
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as tf:
        members = tf.getmembers()
        names = [m.name for m in members]
        if len(members) != 44 or len(set(names)) != 44:
            raise ValueError("archive member count/identity failure")
        if sum(m.size for m in members) != 3912033:
            raise ValueError("unexpected expanded size")
        for m in members:
            p = PurePosixPath(m.name)
            if not m.isfile() or p.is_absolute() or ".." in p.parts or "\\" in m.name:
                raise ValueError("non-regular or unsafe archive member")
        manifest_stream = tf.extractfile("EVIDENCE_MANIFEST.json")
        if manifest_stream is None:
            raise ValueError("missing manifest")
        manifest = json.loads(manifest_stream.read())
        if set(manifest) != set(names) - {"EVIDENCE_MANIFEST.json"}:
            raise ValueError("manifest inventory mismatch")
        for m in members:
            if m.name in manifest:
                stream = tf.extractfile(m)
                if stream is None or digest(stream.read()) != manifest[m.name]:
                    raise ValueError(f"member integrity failure: {m.name}")
        target.mkdir(parents=True, exist_ok=False)
        tf.extractall(target, filter="data")
    for name, expected in manifest.items():
        if digest((target / name).read_bytes()) != expected:
            raise ValueError(f"post-extraction mismatch: {name}")
    return {"status": "PASS_RESTORATION", "members": 44,
            "verified_manifest_files": len(manifest), "sha256": EXPECTED,
            "formal_invocations": 0}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python restore.py NEW_OUTPUT_DIRECTORY")
    try:
        print(json.dumps(restore(Path(__file__).resolve().parent, Path(sys.argv[1])), sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
        raise SystemExit(f"STOP_RESTORATION: {exc}") from exc

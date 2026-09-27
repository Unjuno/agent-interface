"""Bounded, data-only restoration of the retained z7r2 evidence archive."""
from __future__ import annotations
import hashlib, json, tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent


def _safe(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and ".." not in p.parts


def restore(root: Path, out: Path) -> int:
    spec = json.loads((root / "ARCHIVE.json").read_text())
    archive = root / spec["archive"]
    data = archive.read_bytes()
    if len(data) != spec["archive_bytes"]:
        raise ValueError("archive size mismatch")
    if hashlib.sha256(data).hexdigest() != spec["archive_sha256"]:
        raise ValueError("archive hash mismatch")
    if out.exists():
        raise ValueError("destination exists")
    out.mkdir(parents=True)
    regular = 0
    members = 0
    with tarfile.open(archive, mode="r:xz") as tf:
        for m in tf:
            members += 1
            if not _safe(m.name):
                raise ValueError("unsafe member path")
            dst = out / PurePosixPath(m.name)
            if m.isdir():
                dst.mkdir(parents=True, exist_ok=True)
                continue
            if not m.isfile():
                raise ValueError("unsupported member type")
            regular += 1
            if regular > spec["regular_files"]:
                raise ValueError("too many files")
            dst.parent.mkdir(parents=True, exist_ok=True)
            src = tf.extractfile(m)
            if src is None:
                raise ValueError("missing member bytes")
            dst.write_bytes(src.read())
    if regular != spec["regular_files"] or members != spec["tar_members"]:
        raise ValueError("member denominator mismatch")
    return regular

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: restore.py NEW_DESTINATION")
    print(restore(ROOT, Path(sys.argv[1])))
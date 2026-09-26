from __future__ import annotations
import argparse, base64, hashlib, io, os, tarfile
from pathlib import Path

PARTS = [f"evidence.part0{i}.b64" for i in range(1, 8)]
ARCHIVE_SHA256 = "ca08faeea1bcb181b9f10524eca2397d1f54052c47d6c9916997b7a55e54a32d"

def safe_rel(name: str) -> Path:
    p = Path(name)
    if p.is_absolute() or not p.parts or any(x in {"", ".", ".."} for x in p.parts):
        raise ValueError(f"unsafe archive member: {name!r}")
    return p

def restore(here: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"destination exists: {destination}")
    encoded = "".join((here / name).read_text(encoding="ascii").strip() for name in PARTS)
    raw = base64.b64decode(encoded, validate=True)
    got = hashlib.sha256(raw).hexdigest()
    if got != ARCHIVE_SHA256:
        raise ValueError(f"archive sha256 mismatch: {got}")
    destination.mkdir(parents=True)
    root = destination.resolve()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:xz") as tf:
        members = tf.getmembers()
        for m in members:
            rel = safe_rel(m.name)
            if m.issym() or m.islnk() or m.ischr() or m.isblk() or m.isfifo():
                raise ValueError(f"unsupported archive member type: {m.name!r}")
            target = (root / rel).resolve()
            if os.path.commonpath([str(root), str(target)]) != str(root):
                raise ValueError(f"archive path escapes destination: {m.name!r}")
        for m in members:
            rel = safe_rel(m.name)
            target = root / rel
            if m.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif m.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                src = tf.extractfile(m)
                if src is None:
                    raise ValueError(f"missing file payload: {m.name!r}")
                target.write_bytes(src.read())
            else:
                raise ValueError(f"unsupported archive member type: {m.name!r}")
    print(f"restored {len(members)} tar members under {destination}")
    print(f"archive_sha256={ARCHIVE_SHA256}")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("destination", type=Path)
    args = ap.parse_args()
    restore(Path(__file__).resolve().parent, args.destination)

if __name__ == "__main__":
    main()

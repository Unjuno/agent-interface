#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, pathlib, sys, tarfile, tempfile

ROOT = pathlib.Path(__file__).resolve().parent

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_extract(archive, destination):
    with tarfile.open(archive, "r:xz") as tf:
        members = tf.getmembers()
        for m in members:
            p = pathlib.PurePosixPath(m.name)
            if p.is_absolute() or ".." in p.parts or m.issym() or m.islnk():
                raise SystemExit("unsafe archive member: " + m.name)
            if not (m.isfile() or m.isdir()):
                raise SystemExit("unsupported archive member: " + m.name)
        tf.extractall(destination)
        return len([m for m in members if m.isfile()])

def join_verified(rows, expected_size, expected_sha, tmp_path):
    with open(tmp_path, "wb") as out:
        for name, size, sha in rows:
            path = ROOT / name
            if path.stat().st_size != size or digest(path) != sha:
                raise SystemExit("part mismatch: " + name)
            out.write(path.read_bytes())
    if tmp_path.stat().st_size != expected_size or digest(tmp_path) != expected_sha:
        raise SystemExit("reconstructed archive mismatch")

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: unpack.py NEW_DESTINATION")
    dest = pathlib.Path(sys.argv[1]).resolve()
    if dest.exists():
        raise SystemExit("destination must not exist")
    package = json.loads((ROOT / "PACKAGE.json").read_text())
    dest.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        review = td / "review.tar.xz"
        pixels = td / "pixels.tar.xz"
        r = package["review_archive"]
        join_verified(r["parts"], r["size"], r["sha256"], review)
        b = package["bgrx_archive"]
        join_verified(b["parts"], b["size"], b["sha256"], pixels)
        n_review = safe_extract(review, dest)
        n_pixels = safe_extract(pixels, dest)
    if n_review != package["review_archive"]["expanded_files"]:
        raise SystemExit("review member count mismatch")
    if n_pixels != package["bgrx_archive"]["expanded_files"]:
        raise SystemExit("pixel member count mismatch")
    print(json.dumps({
        "status": "verified",
        "review_files": n_review,
        "bgrx_files": n_pixels,
        "destination": str(dest)
    }, sort_keys=True))

if __name__ == "__main__":
    main()

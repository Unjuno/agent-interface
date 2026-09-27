"""Restore hash-bound retained evidence; never run an experiment or import Tk."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import lzma
import tarfile
from pathlib import Path, PurePosixPath

ARCHIVE_SHA256 = "7c06ca65796e4e81cb35c04bb8c96f5a05c5d531de346331075ff02bd376f043"
ARCHIVE_BYTES = 88192
MEMBERS = 315
CONTENT_BYTES = 2162210

def restore(package: Path, out: Path) -> dict:
    if not out.is_absolute() or out.exists():
        raise ValueError("output must be an absent absolute directory")
    meta = json.loads((package / "CAPSULE.json").read_text(encoding="utf-8"))
    expected = [f"part-{i:02d}.bin" for i in range(11)]
    if [p["name"] for p in meta["parts"]] != expected:
        raise ValueError("part order/cardinality mismatch")
    chunks = []
    for part in meta["parts"]:
        data = (package / "evidence" / part["name"]).read_bytes()
        if len(data) != part["bytes"] or hashlib.sha256(data).hexdigest() != part["sha256"]:
            raise ValueError("part bytes mismatch: " + part["name"])
        chunks.append(data)
    packed = b"".join(chunks)
    if len(packed) != ARCHIVE_BYTES or hashlib.sha256(packed).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("archive mismatch")
    # Only a checksum-pinned archive is decoded. No arbitrary archive acceptance.
    raw = lzma.decompress(packed)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        members = archive.getmembers()
        names = set()
        for member in members:
            path = PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or ".." in path.parts
                or "\\" in member.name or member.name in names
                or str(path) != member.name or not path.parts
                or path.parts[0] not in {"previous", "history", "continuation"}):
                raise ValueError("unsafe or duplicate archive member")
            names.add(member.name)
        if len(members) != MEMBERS or sum(m.size for m in members) != CONTENT_BYTES:
            raise ValueError("member count/byte size mismatch")
        out.mkdir(parents=True, exist_ok=False)
        for member in members:
            target = out.joinpath(*PurePosixPath(member.name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("missing regular-file bytes")
            data = source.read()
            if len(data) != member.size:
                raise ValueError("truncated member")
            with target.open("xb") as handle:
                handle.write(data)
    return {"files": MEMBERS, "bytes": CONTENT_BYTES, "archive_sha256": ARCHIVE_SHA256,
            "experiment_executed": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(Path(__file__).resolve().parent, args.out), sort_keys=True))

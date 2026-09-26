"""Restore retained UTF-8 evidence only; never execute a study or overwrite output."""
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import sys


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = value
    return out


def digest(data):
    return hashlib.sha256(data).hexdigest()


def restore(destination):
    here = Path(__file__).resolve().parent
    meta = json.loads((here / "PACK.json").read_bytes(), object_pairs_hook=unique)
    if meta["schema"] != "retained-utf8-map-xz-v1":
        raise ValueError("unknown archive schema")
    if not 0 < meta["packed_bytes"] <= 200000 or not 0 < meta["expanded_bytes"] <= 8388608:
        raise ValueError("archive bound")
    pieces = []
    for item in meta["parts"]:
        name = item["name"]
        if Path(name).name != name or "\\" in name:
            raise ValueError("part path")
        data = (here / name).read_bytes()
        if len(data) != item["bytes"] or digest(data) != item["sha256"]:
            raise ValueError("part integrity")
        pieces.append(data)
    packed = b"".join(pieces)
    if len(packed) != meta["packed_bytes"] or digest(packed) != meta["packed_sha256"]:
        raise ValueError("archive integrity")
    decoder = lzma.LZMADecompressor(memlimit=134217728)
    raw = decoder.decompress(packed, max_length=meta["expanded_bytes"] + 1)
    if not decoder.eof or decoder.unused_data or len(raw) != meta["expanded_bytes"]:
        raise ValueError("expanded extent")
    if digest(raw) != meta["expanded_sha256"]:
        raise ValueError("expanded integrity")
    files = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(files, dict) or len(files) != meta["file_count"] or len(files) > 2000:
        raise ValueError("file denominator")
    values = {}
    for name, text in files.items():
        p = PurePosixPath(name)
        if (not name or p.is_absolute() or str(p) != name or ".." in p.parts
                or "\\" in name or not isinstance(text, str)):
            raise ValueError("member path or type")
        values[name] = text.encode("utf-8")
    if sum(map(len, values.values())) != meta["file_bytes"]:
        raise ValueError("file extent")
    destination = Path(destination)
    destination.mkdir(parents=False, exist_ok=False)
    for name, data in values.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as out:
            out.write(data)
    return {"files": len(values), "bytes": meta["file_bytes"],
            "archive_sha256": meta["packed_sha256"], "executed_study": False}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python unpack.py NEW_DIRECTORY")
    print(json.dumps(restore(sys.argv[1]), sort_keys=True))

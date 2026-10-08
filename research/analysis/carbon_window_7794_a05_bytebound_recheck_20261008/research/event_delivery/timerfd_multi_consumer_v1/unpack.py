"""Bounded data-only restoration of the retained #4056 member bytes."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import lzma
import re
import sys

def need(ok, message):
    if not ok:
        raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def unique(pairs):
    out = {}
    for key, value in pairs:
        need(key not in out, "duplicate JSON key")
        out[key] = value
    return out

def integer(value, limit):
    return type(value) is int and 0 <= value <= limit

def unpack(source, destination):
    source, destination = Path(source), Path(destination)
    need(not destination.exists() and not destination.is_symlink(), "destination exists")
    raw_manifest = (source / "PACK.json").read_bytes()
    need(len(raw_manifest) <= 32000, "manifest too large")
    m = json.loads(raw_manifest, object_pairs_hook=unique)
    need(m["schema"] == "timerfd-ownership-lossless-file-map-v1", "schema")
    need(integer(m["file_count"], 1000) and m["file_count"] == 289, "file count")
    need(integer(m["file_bytes"], 4000000), "member size")
    need(integer(m["expanded_bytes"], 4000000), "expansion size")
    need(integer(m["capsule_bytes"], 200000), "capsule size")
    need(type(m["parts"]) is list and 0 < len(m["parts"]) <= 40, "parts")
    blocks = []
    for i, part in enumerate(m["parts"]):
        need(part["path"] == f"parts/{i:03d}.bin", "part order/path")
        need(integer(part["bytes"], 10000), "part size")
        path = source / part["path"]
        need(path.is_file() and not path.is_symlink(), "part not regular")
        data = path.read_bytes()
        need(len(data) == part["bytes"] and digest(data) == part["sha256"], "part integrity")
        blocks.append(data)
    packed = b"".join(blocks)
    need(len(packed) == m["capsule_bytes"] and digest(packed) == m["capsule_sha256"], "capsule integrity")
    dec = lzma.LZMADecompressor(memlimit=256 * 1024 * 1024)
    expanded = dec.decompress(packed, max_length=m["expanded_bytes"] + 1)
    need(dec.eof and not dec.unused_data, "trailing or truncated XZ")
    need(len(expanded) == m["expanded_bytes"] and digest(expanded) == m["expanded_sha256"], "expanded integrity")
    members = json.loads(expanded, object_pairs_hook=unique)
    need(type(members) is dict and len(members) == m["file_count"], "member count")
    files, total = {}, 0
    for name, text in members.items():
        need(type(name) is str and type(text) is str, "member types")
        p = PurePosixPath(name)
        need(name and not p.is_absolute() and str(p) == name, "member path")
        need("\\" not in name and "\x00" not in name and all(x not in (".", "..", "") for x in p.parts), "unsafe member")
        need(len(name) <= 512, "long path")
        data = text.encode("utf-8")
        total += len(data)
        need(total <= 4000000, "members too large")
        files[name] = data
    need(total == m["file_bytes"], "member byte count")
    for name in files:
        need(not any(str(p) in files for p in PurePosixPath(name).parents if str(p) != "."), "file/directory collision")
    destination.mkdir(parents=False, exist_ok=False)
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    return {"files": len(files), "bytes": total, "capsule_sha256": digest(packed)}

if __name__ == "__main__":
    try:
        need(len(sys.argv) == 2, "usage: unpack.py NEW_DIRECTORY")
        print(json.dumps(unpack(Path(__file__).resolve().parent, Path(sys.argv[1])), sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, lzma.LZMAError) as error:
        print(f"UNPACK_REFUSED: {error}", file=sys.stderr)
        raise SystemExit(1)

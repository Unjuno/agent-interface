"""Restore retained Inkscape evidence as data; never import or run archived code."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath

MAX_ARCHIVE = 262144
MAX_EXPANDED = 4194304
MAX_FILES = 1000
MAX_MEMBER_BYTES = 3145728

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def decode(directory: Path) -> dict[str, bytes]:
    manifest = json.loads((directory / "ARCHIVE.json").read_bytes(), object_pairs_hook=unique_object)
    require(manifest["format"] == "xz-tagged-file-map-v1", "format")
    for key, maximum in (("archive_bytes", MAX_ARCHIVE), ("expanded_bytes", MAX_EXPANDED),
                         ("members", MAX_FILES), ("member_bytes", MAX_MEMBER_BYTES)):
        value = manifest[key]
        require(type(value) is int and 0 < value <= maximum, "invalid bound: " + key)
    parts = manifest["parts"]
    require(type(parts) is list and 0 < len(parts) <= 32, "parts")
    blocks = []
    names = set()
    total = 0
    for part in parts:
        name = part["path"]
        require(type(name) is str and name == PurePosixPath(name).name and "\\" not in name
                and name not in ("", ".", "..") and name not in names, "part path")
        names.add(name)
        path = directory / name
        require(path.is_file() and not path.is_symlink(), "nonregular part")
        size = part["bytes"]
        require(type(size) is int and 0 < size <= MAX_ARCHIVE, "part size")
        require(path.stat().st_size == size, "part size mismatch")
        block = path.read_bytes()
        require(len(block) == size and digest(block) == part["sha256"], "part digest")
        total += len(block)
        require(total <= MAX_ARCHIVE, "archive bound")
        blocks.append(block)
    archive = b"".join(blocks)
    require(len(archive) == manifest["archive_bytes"] and digest(archive) == manifest["archive_sha256"],
            "archive identity")
    decoder = lzma.LZMADecompressor(memlimit=134217728)
    payload = decoder.decompress(archive, max_length=manifest["expanded_bytes"] + 1)
    require(decoder.eof and not decoder.unused_data and len(payload) == manifest["expanded_bytes"],
            "expansion size or trailing data")
    entries = json.loads(payload, object_pairs_hook=unique_object)
    require(type(entries) is dict and len(entries) == manifest["members"], "member count")
    files = {}
    size_total = 0
    for name, item in entries.items():
        require(type(name) is str and "\\" not in name and "\0" not in name, "member path type")
        path = PurePosixPath(name)
        require(not path.is_absolute() and path.parts and str(path) == name
                and all(p not in ("", ".", "..") for p in path.parts), "member path")
        require(type(item) is list and len(item) == 2 and type(item[1]) is str, "member encoding")
        if item[0] == "text":
            data = item[1].encode("utf-8")
        elif item[0] == "base64":
            data = base64.b64decode(item[1], validate=True)
        else:
            raise ValueError("unknown member encoding")
        size_total += len(data)
        require(size_total <= MAX_MEMBER_BYTES, "member byte bound")
        files[name] = data
    require(size_total == manifest["member_bytes"], "member byte count")
    require("SHA256SUMS" in files, "missing original manifest")
    seen = set()
    for line in files["SHA256SUMS"].decode("utf-8").splitlines():
        expected, name = line.split("  ", 1)
        require(name in files and name not in seen and name != "SHA256SUMS", "manifest member")
        require(digest(files[name]) == expected, "original member digest: " + name)
        seen.add(name)
    require(seen == set(files) - {"SHA256SUMS"}, "original manifest coverage")
    return files

def restore(directory: Path, destination: Path) -> dict:
    require(not destination.exists() and not destination.is_symlink(), "destination exists")
    files = decode(directory)
    destination.mkdir(parents=False, exist_ok=False)
    for name, data in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
    return {"decision": "PASS_BYTE_EXACT_RESTORATION", "files": len(files),
            "member_bytes": sum(map(len, files.values())), "code_executed": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(Path(__file__).resolve().parent, args.destination), sort_keys=True))

#!/usr/bin/env python3
"""Bounded, non-executing restoration of the exact Issue 4001 evidence."""
import base64
import hashlib
import json
import lzma
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result

def main(destination):
    manifest = json.loads((HERE/"BUNDLE.json").read_text(), object_pairs_hook=unique)
    packed = base64.b64decode(b"".join((HERE/name).read_bytes() for name in manifest["encoded_parts"]), validate=True)
    if len(packed) != manifest["compressed_bytes"] or sha(packed) != manifest["compressed_sha256"]:
        raise ValueError("archive identity mismatch")
    decoder = lzma.LZMADecompressor(memlimit=64*1024*1024)
    data = decoder.decompress(packed, max_length=manifest["decoded_bytes"]+1)
    if not decoder.eof or decoder.unused_data or len(data) != manifest["decoded_bytes"] or sha(data) != manifest["decoded_sha256"]:
        raise ValueError("decode boundary/identity mismatch")
    files = json.loads(data, object_pairs_hook=unique)
    if set(files) != set(manifest["members"]):
        raise ValueError("member set mismatch")
    for name, text in files.items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or not path.parts or "\\" in name:
            raise ValueError("unsafe path")
        payload = text.encode("utf-8")
        spec = manifest["members"][name]
        if len(payload) != spec["bytes"] or sha(payload) != spec["sha256"]:
            raise ValueError("member identity mismatch: "+name)
    destination = Path(destination)
    destination.mkdir(parents=False, exist_ok=False)
    for name, text in files.items():
        path = destination/name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(text.encode("utf-8"))
    print(json.dumps({"restored_files": len(files), "bytes_verified": len(data),
                      "destination": str(destination), "code_executed": False}, sort_keys=True))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: unpack.py ABSENT_DESTINATION")
    main(sys.argv[1])

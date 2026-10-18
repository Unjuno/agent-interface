#!/usr/bin/env python3
"""Reconstruct and verify exact gzip-transported A01 formal files."""
import gzip
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent / "formal"
manifest = json.loads((root / "FORMAL_MANIFEST.json").read_text(encoding="utf-8"))
ok = True
for name, entry in manifest.items():
    if not isinstance(entry, dict):
        continue
    if name == "child_streams":
        for child_name, child_entry in entry.items():
            data = (root / child_name).read_bytes()
            if (len(data) != child_entry["bytes"] or
                    hashlib.sha256(data).hexdigest() != child_entry["sha256"]):
                raise SystemExit("stream_digest_mismatch:" + child_name)
            print("PASS %s %d %s" % (child_name, len(data), child_entry["sha256"]))
        continue
    if "transport" not in entry:
        data = (root / name).read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise SystemExit("stream_digest_mismatch:" + name)
        print("PASS %s %d %s" % (name, len(data), entry["sha256"]))
        continue
    compressed = (root / entry["transport"]).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != entry["gzip_sha256"]:
        raise SystemExit("gzip_digest_mismatch:" + name)
    data = gzip.decompress(compressed)
    if len(data) != entry["uncompressed_bytes"]:
        raise SystemExit("byte_count_mismatch:" + name)
    if hashlib.sha256(data).hexdigest() != entry["uncompressed_sha256"]:
        raise SystemExit("raw_digest_mismatch:" + name)
    if len(sys.argv) > 1:
        target = pathlib.Path(sys.argv[1]) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print("PASS %s %d %s" % (name, len(data), entry["uncompressed_sha256"]))

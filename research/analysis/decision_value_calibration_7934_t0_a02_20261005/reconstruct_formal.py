#!/usr/bin/env python3
"""Reconstruct and verify A02 formal evidence without rerunning it."""
import gzip
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent / "formal"
manifest = json.loads((root / "FORMAL_MANIFEST.json").read_text(encoding="utf-8"))


def canonical_text_bytes(path):
    """Undo Git's Windows CRLF checkout conversion before checking text hashes."""
    return path.read_bytes().replace(b"\r\n", b"\n")


raw_parts = []
for part in manifest["raw"]["parts"]:
    packed = (root / part["path"]).read_bytes()
    if len(packed) != part["bytes"] or hashlib.sha256(packed).hexdigest() != part["sha256"]:
        raise SystemExit("part_transport_digest:" + part["path"])
    data = gzip.decompress(packed)
    if len(data) != part["raw_bytes"] or hashlib.sha256(data).hexdigest() != part["raw_sha256"]:
        raise SystemExit("part_raw_digest:" + part["path"])
    if len(data.splitlines()) != part["rows"]:
        raise SystemExit("part_row_count:" + part["path"])
    raw_parts.append(data)
raw = b"".join(raw_parts)
if len(raw) != manifest["raw"]["bytes"] or hashlib.sha256(raw).hexdigest() != manifest["raw"]["sha256"]:
    raise SystemExit("combined_raw_digest")
candidate_entry = manifest["candidate_result"]
candidate_gz = (root / candidate_entry.get("transport", "candidate_result.json.gz")).read_bytes()
if (len(candidate_gz) != candidate_entry["gzip_bytes"] or
        hashlib.sha256(candidate_gz).hexdigest() != candidate_entry["gzip_sha256"]):
    raise SystemExit("candidate_transport_digest")
candidate = gzip.decompress(candidate_gz)
if (len(candidate) != candidate_entry["uncompressed_bytes"] or
        hashlib.sha256(candidate).hexdigest() != candidate_entry["uncompressed_sha256"]):
    raise SystemExit("candidate_result_digest")
terminal = canonical_text_bytes(root / "terminal.json")
if hashlib.sha256(terminal).hexdigest() != manifest["terminal_sha256"]:
    raise SystemExit("terminal_digest")
for name, entry in manifest["streams"].items():
    data = canonical_text_bytes(root / name)
    if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise SystemExit("stream_digest:" + name)
if len(sys.argv) > 1:
    dest = pathlib.Path(sys.argv[1])
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "raw_observations.jsonl").write_bytes(raw)
    (dest / "candidate_result.json").write_bytes(candidate)
print("PASS raw=%d rows=%d candidate=%d" %
      (len(raw), manifest["raw"]["rows"], len(candidate)))

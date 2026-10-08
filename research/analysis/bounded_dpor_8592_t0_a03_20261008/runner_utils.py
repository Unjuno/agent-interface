"""Integrity helpers for frozen candidate/auditor invocations."""

import hashlib
import json
from pathlib import Path


def verify_manifest(package_root, manifest):
    root = Path(package_root).resolve()
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("freeze manifest has no file hashes")
    for relative, expected in files.items():
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ValueError(f"freeze path escapes package: {relative}") from error
        if not path.is_file():
            raise ValueError(f"frozen source missing: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"hash mismatch: {relative}")

def write_json_once(path, value):
    target = Path(path)
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")

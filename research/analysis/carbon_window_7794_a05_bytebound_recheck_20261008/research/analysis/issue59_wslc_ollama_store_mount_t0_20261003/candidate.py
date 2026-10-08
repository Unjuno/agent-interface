#!/usr/bin/env python3
"""One-shot read-only inventory of selected Ollama manifests in a mounted store."""
import argparse
import hashlib
import json
import re
import stat
import sys
from pathlib import Path

DIGEST_RE = re.compile(r"^sha256:([0-9a-f]{64})$")


def mount_record(mountinfo: str, target: str):
    found = []
    for line in mountinfo.splitlines():
        fields = line.split()
        if len(fields) >= 6 and fields[4].replace("\\040", " ") == target:
            options = fields[5].split(",")
            found.append({"mountpoint": target, "options": options,
                          "readonly": "ro" in options and "rw" not in options})
    if len(found) != 1:
        return {"mountpoint": target, "options": [], "readonly": False,
                "matching_mount_records": len(found)}
    found[0]["matching_mount_records"] = 1
    return found[0]


def inspect(fixture_path: Path, model_root: Path):
    fixture_bytes = fixture_path.read_bytes()
    fixture = json.loads(fixture_bytes)
    mount = mount_record(Path("/proc/self/mountinfo").read_text(encoding="utf-8"), "/models")
    observed_models = []
    errors = []
    for expected in fixture["models"]:
        manifest_path = model_root / expected["manifest_rel"]
        if not manifest_path.is_file() or manifest_path.is_symlink():
            observed_models.append({"name": expected["name"], "present": False})
            errors.append("manifest_missing:" + expected["name"])
            continue
        manifest_bytes = manifest_path.read_bytes()
        doc = json.loads(manifest_bytes)
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        descriptors = [doc.get("config", {}), *doc.get("layers", [])]
        blobs = []
        for descriptor in descriptors:
            digest = descriptor.get("digest", "")
            match = DIGEST_RE.fullmatch(digest)
            if not match:
                errors.append("invalid_descriptor_digest:" + expected["name"])
                blobs.append({"digest": digest, "present": False, "bytes": None})
                continue
            rel = "blobs/sha256-" + match.group(1)
            blob_path = model_root / rel
            exists = blob_path.is_file() and not blob_path.is_symlink()
            actual_size = blob_path.stat().st_size if exists else None
            blobs.append({"digest": digest, "path": rel, "declared_bytes": descriptor.get("size"),
                          "present": exists, "observed_bytes": actual_size})
            if not exists:
                errors.append("blob_missing:" + expected["name"] + ":" + digest)
            elif actual_size != descriptor.get("size"):
                errors.append("blob_size_mismatch:" + expected["name"] + ":" + digest)
        observed_models.append({"name": expected["name"], "present": True,
                                "manifest_rel": expected["manifest_rel"],
                                "manifest_sha256": manifest_sha,
                                "schema_version": doc.get("schemaVersion"),
                                "media_type": doc.get("mediaType"), "blobs": blobs})
    result = {"schema_version": 1,
              "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
              "mount": mount, "models": observed_models, "errors": errors,
              "blob_content_hashed": False, "model_loaded": False,
              "network_requested": False}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("model_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = inspect(args.fixture, args.model_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"mount_readonly": result["mount"]["readonly"],
                      "models": len(result["models"]), "errors": len(result["errors"])}))
    return 0 if result["mount"]["readonly"] and not result["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

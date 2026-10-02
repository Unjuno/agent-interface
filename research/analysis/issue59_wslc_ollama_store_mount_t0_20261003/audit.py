#!/usr/bin/env python3
"""Independent raw-only check for the Ollama model-store mount probe."""
import argparse
import hashlib
import json
from pathlib import Path


def validate(fixture_bytes: bytes, raw: dict):
    errors = []
    try:
        fixture = json.loads(fixture_bytes)
    except Exception as exc:
        return ["fixture_invalid:" + type(exc).__name__]
    if raw.get("schema_version") != 1:
        errors.append("schema_version")
    if raw.get("fixture_sha256") != hashlib.sha256(fixture_bytes).hexdigest():
        errors.append("fixture_hash")
    mount = raw.get("mount", {})
    if mount.get("mountpoint") != "/models" or mount.get("matching_mount_records") != 1:
        errors.append("mount_identity")
    options = mount.get("options", [])
    if "ro" not in options or "rw" in options or mount.get("readonly") is not True:
        errors.append("mount_not_readonly")
    if raw.get("blob_content_hashed") is not False or raw.get("model_loaded") is not False:
        errors.append("scope_violation")
    expected = {model["name"]: model for model in fixture.get("models", [])}
    observed_rows = raw.get("models", [])
    observed_names = [row.get("name") for row in observed_rows]
    if len(observed_names) != len(set(observed_names)) or set(observed_names) != set(expected):
        errors.append("model_coverage")
    by_name = {row.get("name"): row for row in observed_rows}
    for name, model in expected.items():
        row = by_name.get(name)
        if row is None:
            continue
        if row.get("present") is not True or row.get("manifest_rel") != model["manifest_rel"]:
            errors.append("manifest_presence:" + name)
        if row.get("manifest_sha256") != model["manifest_sha256"]:
            errors.append("manifest_sha256:" + name)
        if row.get("schema_version") != model["schema_version"] or row.get("media_type") != model["media_type"]:
            errors.append("manifest_header:" + name)
        expected_blobs = {layer["digest"]: layer for layer in model["blobs"]}
        observed_blobs = row.get("blobs", [])
        observed_digests = [blob.get("digest") for blob in observed_blobs]
        if len(observed_digests) != len(set(observed_digests)) or set(observed_digests) != set(expected_blobs):
            errors.append("blob_coverage:" + name)
        by_digest = {blob.get("digest"): blob for blob in observed_blobs}
        for digest, layer in expected_blobs.items():
            blob = by_digest.get(digest)
            if blob is None:
                continue
            if (blob.get("path") != layer["path"] or blob.get("present") is not True
                    or blob.get("declared_bytes") != layer["size"]
                    or blob.get("observed_bytes") != layer["size"]):
                errors.append("blob_identity_or_size:" + name + ":" + digest)
    if raw.get("errors") != []:
        errors.append("candidate_errors_not_empty")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    errors = validate(args.fixture.read_bytes(), json.loads(args.raw.read_text(encoding="utf-8")))
    result = {"status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
              "errors": errors,
              "fixture_sha256": hashlib.sha256(args.fixture.read_bytes()).hexdigest(),
              "raw_sha256": hashlib.sha256(args.raw.read_bytes()).hexdigest()}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": len(errors)}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

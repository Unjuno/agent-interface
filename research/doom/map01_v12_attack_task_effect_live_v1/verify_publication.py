#!/usr/bin/env python3
"""Recompute publication and source-capsule integrity without runner imports."""
import hashlib
import io
import json
import lzma
import tarfile
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_recheck_manifest(root):
    errors = []
    for line in (root / "INTEGRITY_RECHECK_SHA256SUMS").read_text().splitlines():
        expected, name = line.split(None, 1)
        relative = Path(name.strip())
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"integrity_manifest_unsafe:{name}")
            continue
        path = root / relative
        if not path.is_file() or sha(path.read_bytes()) != expected:
            errors.append(f"integrity_manifest:{name.strip()}")
    return errors


def verify(root):
    errors = verify_recheck_manifest(root)
    read = lambda name: (root / name).read_bytes()
    publication = json.loads(read("PUBLICATION.json"))
    freeze = json.loads(read("FREEZE.json"))
    result = json.loads(read("RESULT.json"))
    audit = json.loads(read("AUDIT_SUMMARY.json"))
    report = read("REPORT.md")
    raw_xz = read("RAW_USED.json.xz")
    source_xz = read("SOURCE.tar.xz")

    decoded_raw = lzma.decompress(raw_xz)
    source_files = {}
    with tarfile.open(fileobj=io.BytesIO(source_xz), mode="r:xz") as archive:
        for member in archive.getmembers():
            if not member.isfile() or member.name.startswith("/") or ".." in Path(member.name).parts:
                errors.append("unsafe_source_member")
                continue
            stream = archive.extractfile(member)
            if stream is None:
                errors.append("unreadable_source_member")
                continue
            source_files[member.name] = stream.read()

    sidecar = {}
    for line in read("SHA256SUMS.source").decode().splitlines():
        digest, name = line.split(None, 1)
        sidecar[name.strip()] = digest

    expected_hashes = {
        "result_summary_sha256": ("RESULT.json", sha(read("RESULT.json"))),
        "audit_summary_sha256": ("AUDIT_SUMMARY.json", sha(read("AUDIT_SUMMARY.json"))),
        "report_sha256": ("REPORT.md", sha(report)),
    }
    for key, (name, actual) in expected_hashes.items():
        if publication.get(key) != actual:
            errors.append(f"publication:{key}")
    if publication.get("raw_used", {}).get("sha256") != sha(raw_xz):
        errors.append("raw_compressed_sha256")
    if publication.get("raw_used", {}).get("decoded_sha256") != sha(decoded_raw):
        errors.append("raw_decoded_sha256")
    if publication.get("raw_used", {}).get("decoded_bytes") != len(decoded_raw):
        errors.append("raw_decoded_bytes")
    if sha(source_xz) != freeze.get("source_capsule_sha256"):
        errors.append("source_capsule_sha256")
    if len(source_files) != len(sidecar) or set(source_files) != set(sidecar):
        errors.append("source_member_set")
    for name, data in source_files.items():
        digest = sha(data)
        if sidecar.get(name) != digest:
            errors.append(f"sidecar:{name}")
        if freeze.get("source_sha256", {}).get(name) != digest:
            errors.append(f"freeze:{name}")
    for name, expected in freeze.get("source_sha256", {}).items():
        if name not in source_files:
            if not (root / name).is_file():
                errors.append(f"freeze_external_missing:{name}")
            elif sha(read(name)) != expected:
                errors.append(f"freeze_external:{name}")
    if result.get("decision") != "HOLD_ATTACK_TASK_EFFECT_NOT_REPRODUCED":
        errors.append("decision")
    if result.get("formal_invocations") != 1 or result.get("reruns") != 0 or result.get("replacements") != 0 or result.get("tuning_after_freeze") != 0:
        errors.append("formal_counts")
    if result.get("attack_bound_effect_counts") != [0, 0, 0] or result.get("no_input_positive_effect_counts") != [0, 0, 0]:
        errors.append("effect_counts")
    if audit.get("decision") != result.get("decision") or audit.get("errors") != []:
        errors.append("audit_summary")
    return {"gate_groups": 11, "errors": errors, "source_files": sorted(source_files), "raw_rows": 6}


if __name__ == "__main__":
    import sys
    output = verify(Path(sys.argv[1]))
    print(json.dumps(output, sort_keys=True))
    raise SystemExit(bool(output["errors"]))

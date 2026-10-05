"""Verify the retained current-final F03 archive and frozen member hashes."""
from __future__ import annotations

import hashlib
import re
import tarfile
from pathlib import Path

from freeze_lineage_v1 import verify_lineage

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "f03-formal-freeze-6d8387caa8.tar"
FREEZE_MANIFEST = HERE / "freeze-manifests" / "PRELAUNCH_FREEZE-43f9a0008bf7.md"
EXPECTED_FREEZE_COMMIT = "43f9a0008bf75da19865cfdea2898d1b896fbbc3"
EXPECTED_FREEZE_TREE = "2a8c0d1858d237eb0405101e137b39909dff4c5e"
EXPECTED_FREEZE_BLOB_SHA1 = "526a5a066d3bcc5f348b5415cfebc3e53eea706a"
EXPECTED_FREEZE_SHA256 = "4f3abb18ddd8fa0d2248531fa0381d542fe740a4863310100c5820dde5767da1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def frozen_manifest() -> tuple[str, dict[str, str]]:
    raw = FREEZE_MANIFEST.read_bytes()
    if sha256(raw) != EXPECTED_FREEZE_SHA256:
        raise ValueError("current-final freeze snapshot SHA-256 mismatch")
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if blob != EXPECTED_FREEZE_BLOB_SHA1:
        raise ValueError(f"current-final freeze Git blob mismatch: {blob}")

    manifest = raw.decode("utf-8")
    archive_matches = re.findall(
        r"Exact eight-file archive SHA-256: `([0-9a-f]{64})`", manifest
    )
    member_pairs = re.findall(r"(?m)^([0-9a-f]{64})  (research/[^\n]+)$", manifest)
    if len(archive_matches) != 1 or len(member_pairs) != 8:
        raise ValueError("current-final freeze archive/member manifest is malformed")
    return archive_matches[0], {path: digest for digest, path in member_pairs}


def verify(archive: Path = ARCHIVE) -> dict:
    expected_archive_sha256, expected_members = frozen_manifest()
    archive_bytes = archive.read_bytes()
    observed_archive_hash = sha256(archive_bytes)
    if observed_archive_hash != expected_archive_sha256:
        raise ValueError(f"outer archive hash mismatch: {observed_archive_hash}")

    observed_members = {}
    member_bytes = {}
    with tarfile.open(archive, mode="r:") as bundle:
        for member in bundle.getmembers():
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"unsupported archive member type: {member.name}")
            stream = bundle.extractfile(member)
            if stream is None:
                raise ValueError(f"unreadable archive member: {member.name}")
            member_data = stream.read()
            member_bytes[member.name] = member_data
            observed_members[member.name] = sha256(member_data)

    if observed_members != expected_members:
        raise ValueError("archive member set or member hash mismatch")
    lineage = verify_lineage("current_final", member_bytes)
    if observed_archive_hash != lineage["archive_sha256_from_manifest"]:
        raise ValueError("archive digest does not match the authenticated freeze manifest")
    return {
        "archive_sha256": observed_archive_hash,
        "archive_size_bytes": len(archive_bytes),
        "member_count": len(observed_members),
        "freeze_lineage": lineage,
        "freeze_manifest_source_commit": EXPECTED_FREEZE_COMMIT,
        "freeze_manifest_source_tree": EXPECTED_FREEZE_TREE,
        "freeze_manifest_git_blob": EXPECTED_FREEZE_BLOB_SHA1,
        "freeze_manifest_sha256": EXPECTED_FREEZE_SHA256,
        "member_hashes_match": True,
        "status": "PASS_F03_CURRENT_FINAL_ARCHIVE_BYTES_MEMBERS_AND_MANIFEST",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(verify(), indent=2))

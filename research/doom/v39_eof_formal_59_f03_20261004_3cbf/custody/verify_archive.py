"""Verify the retained F03 source archive bytes and all frozen member hashes."""
from __future__ import annotations

import hashlib
import re
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "f03-final-freeze-40b57f74f4.tar"
FREEZE_MANIFEST = HERE / "freeze-manifests" / "PRELAUNCH_FREEZE-fe2dbe361940.md"
EXPECTED_FREEZE_COMMIT = "fe2dbe3619403b4b356bc0bd365f548a21030812"
EXPECTED_FREEZE_TREE = "868b6ef0d40e73a429e92d5127fbfac05b40c366"
EXPECTED_FREEZE_BLOB_SHA1 = "8a8fab7ec3da0c6b9fac17cff87c50b228b93b87"
EXPECTED_FREEZE_SHA256 = "bf812996ae896282ba9bc311fa68cb65206d3e5984ff958710fe73b382fb90a1"


def frozen_manifest() -> tuple[str, dict[str, str]]:
    raw = FREEZE_MANIFEST.read_bytes()
    if sha256(raw) != EXPECTED_FREEZE_SHA256:
        raise ValueError("historical freeze snapshot SHA-256 mismatch")
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if blob != EXPECTED_FREEZE_BLOB_SHA1:
        raise ValueError(f"historical freeze Git blob mismatch: {blob}")

    manifest = raw.decode("utf-8")
    archive_matches = re.findall(
        r"Exact eight-file archive SHA-256: `([0-9a-f]{64})`", manifest
    )
    member_pairs = re.findall(r"(?m)^([0-9a-f]{64})  (research/[^\n]+)$", manifest)
    if len(archive_matches) != 1 or len(member_pairs) != 8:
        raise ValueError("historical freeze archive/member manifest is malformed")
    expected_members = {path: digest for digest, path in member_pairs}
    return archive_matches[0], expected_members


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(archive: Path = ARCHIVE) -> dict:
    expected_archive_sha256, expected_members = frozen_manifest()
    archive_bytes = archive.read_bytes()
    observed_archive_hash = sha256(archive_bytes)
    if observed_archive_hash != expected_archive_sha256:
        raise ValueError(f"outer archive hash mismatch: {observed_archive_hash}")

    observed_members = {}
    with tarfile.open(archive, mode="r:") as bundle:
        for member in bundle.getmembers():
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"unsupported archive member type: {member.name}")
            stream = bundle.extractfile(member)
            if stream is None:
                raise ValueError(f"unreadable archive member: {member.name}")
            observed_members[member.name] = sha256(stream.read())

    if observed_members != expected_members:
        raise ValueError("archive member set or member hash mismatch")
    return {"archive_sha256": observed_archive_hash,
            "archive_size_bytes": len(archive_bytes),
            "member_count": len(observed_members),
            "freeze_manifest_source_commit": EXPECTED_FREEZE_COMMIT,
            "freeze_manifest_source_tree": EXPECTED_FREEZE_TREE,
            "freeze_manifest_git_blob": EXPECTED_FREEZE_BLOB_SHA1,
            "freeze_manifest_sha256": EXPECTED_FREEZE_SHA256,
            "member_hashes_match": True,
            "status": "PASS_F03_ARCHIVE_BYTES_MEMBERS_AND_HISTORICAL_MANIFEST"}


if __name__ == "__main__":
    import json
    print(json.dumps(verify(), indent=2))

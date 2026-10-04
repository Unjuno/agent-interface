"""Verify the retained F03 source archive bytes and all frozen member hashes."""
from __future__ import annotations

import hashlib
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "f03-final-freeze-40b57f74f4.tar"
EXPECTED_ARCHIVE_SHA256 = (
    "a70555a7c3c356c3c0175abb9a4a8497df5cfe93bdaf1b71082169cdb6bddcc9"
)
EXPECTED_MEMBERS = {
    "research/doom/v39_eof_formal_59_f03_20261004_3cbf/runner.py":
        "623fc63fb7d7f0ea87bd39109eb0a1bdcb5da7d5615cca2f85fcf2921821d386",
    "research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit.py":
        "fd6d766f162ce7bc4e42890bb720245fc906ea11985303b0b9b97dd30203d5d2",
    "research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit_saved.py":
        "ebfcef6197e7f121c9eb7d1c6822ac5d6fc3c1c9c3a4b2530517ad8a6de6d1d6",
    "research/doom/v39_eof_formal_59_f03_20261004_3cbf/PROTOCOL.md":
        "4438143d2ae3b8ea5448ffb9f6fd4ebe6c57785dc53951f6e2f35c0d32784d68",
    "research/doom/v39_eof_formal_59_f03_20261004_3cbf/CUSTODY_PROTOCOL.md":
        "fc38b137d3140b7c6951e3481762598922f30c27316721a9af4610751227a1d2",
    "research/doom/v39_eof_59_f02_20261004_3cbf/candidate.py":
        "2b569e6697720bef1f9d0381af6bc4876770132f26e418f697f136c40fc8a1a1",
    "research/doom/v39_os_pipe_59_f01_20261004_3cbf/probe.py":
        "8359de6a8c714eabc08e88b6d22d51935be23fc3cfde5663fdc85bf44d1d1ae0",
    "research/doom/v39_native_fault_59_e05_20261004_3cbf/source-closure.tar.gz":
        "d1ad6dcb8720b27766702361b4898d13259d2efe0b173e7d0fbc970fe3d988db",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(archive: Path = ARCHIVE) -> dict:
    archive_bytes = archive.read_bytes()
    observed_archive_hash = sha256(archive_bytes)
    if observed_archive_hash != EXPECTED_ARCHIVE_SHA256:
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

    if observed_members != EXPECTED_MEMBERS:
        raise ValueError("archive member set or member hash mismatch")
    return {"archive_sha256": observed_archive_hash,
            "archive_size_bytes": len(archive_bytes),
            "member_count": len(observed_members),
            "member_hashes_match": True,
            "status": "PASS_F03_ARCHIVE_BYTES_AND_MEMBERS"}


if __name__ == "__main__":
    import json
    print(json.dumps(verify(), indent=2))

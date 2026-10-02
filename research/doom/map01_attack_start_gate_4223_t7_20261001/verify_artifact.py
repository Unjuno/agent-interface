"""Verify and safely unpack the immutable offline runtime artifact."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import zipfile


ARTIFACT_ID = 10398313098
ARTIFACT_SHA256 = "522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b"
SOURCE_BASE = "9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_rel(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(p in ("", ".", "..") for p in path.parts):
        raise ValueError(f"unsafe archive member: {name!r}")
    return path


def verify_and_unpack(zip_path: Path, destination: Path) -> dict:
    if sha(zip_path) != ARTIFACT_SHA256:
        raise ValueError("offline runtime ZIP SHA-256 mismatch")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("destination must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
        expected_zip_names = {"manifest.json", "source.tar.gz", *manifest.get("wheels", {})}
        if names != expected_zip_names:
            raise ValueError("runtime artifact ZIP member closure mismatch")
        if manifest.get("base_commit") != SOURCE_BASE or manifest.get("experiment_executed") is not False:
            raise ValueError("runtime source base/experiment status mismatch")
        if len(manifest.get("files", {})) != 2592:
            raise ValueError("runtime source manifest file count mismatch")
        source_tar = destination / "source.tar.gz"
        source_tar.write_bytes(archive.read("source.tar.gz"))
        (destination / "manifest.json").write_bytes(archive.read("manifest.json"))
        wheels_root = destination / "wheels"
        wheels_root.mkdir()
        wheel_rows = manifest.get("wheels", {})
        actual_wheel_names = {n for n in names if n.startswith("wheels/")}
        if actual_wheel_names != set(wheel_rows):
            raise ValueError("wheel manifest closure mismatch")
        for name, row in wheel_rows.items():
            rel = safe_rel(name)
            data = archive.read(name)
            if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError(f"wheel identity mismatch: {name}")
            target = destination.joinpath(*rel.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

    source_root = destination / "source"
    source_root.mkdir()
    with tarfile.open(source_tar, "r:gz") as archive:
        members = archive.getmembers()
        expected = set(manifest["files"])
        actual: set[str] = set()
        for member in members:
            rel = safe_rel(member.name.removeprefix("./"))
            if not member.isfile():
                raise ValueError(f"non-regular source archive member: {member.name}")
            name = rel.as_posix()
            if name in actual:
                raise ValueError(f"duplicate source archive member: {name}")
            actual.add(name)
            row = manifest["files"].get(name)
            if row is None or member.size != row["bytes"]:
                raise ValueError(f"source manifest mismatch: {name}")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"unreadable source archive member: {name}")
            data = stream.read()
            if hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError(f"source content mismatch: {name}")
            target = source_root.joinpath(*rel.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if actual != expected:
            raise ValueError(f"source closure mismatch: expected {len(expected)} got {len(actual)}")
    for required in (
        "research/doom/session_map01_v13.py",
        "research/doom/session_map01_v12.py",
        "research/doom/doom_retained_input_backend_v3.py",
    ):
        if not (source_root / required).is_file():
            raise ValueError(f"required runtime source absent: {required}")
    result = {
        "artifact_id": ARTIFACT_ID,
        "artifact_sha256": ARTIFACT_SHA256,
        "runtime_source_base": SOURCE_BASE,
        "manifest_source_files": len(manifest["files"]),
        "verified_source_files": len(actual),
        "verified_wheels": len(wheel_rows),
        "source_tar_sha256": sha(source_tar),
    }
    (destination / "ARTIFACT_VERIFICATION.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result

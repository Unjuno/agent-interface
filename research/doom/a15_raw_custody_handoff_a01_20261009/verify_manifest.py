"""Verify the sanitized A15 custody manifest against a retained local run."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(raw_root, manifest_path, readback_path, public_summary_path,
           public_repo=None, public_revision=None):
    raw_root = Path(raw_root).resolve(strict=True)
    manifest_bytes = Path(manifest_path).read_bytes()
    readback = json.loads(Path(readback_path).read_text(encoding="utf-8"))
    if readback.get("manifest_sha256") != sha256_bytes(manifest_bytes):
        raise ValueError("manifest digest mismatch")
    if readback.get("manifest_entries") != len(manifest_bytes.splitlines()):
        raise ValueError("manifest entry count mismatch")

    entries = []
    seen = set()
    total_bytes = 0
    for line_number, line in enumerate(manifest_bytes.splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL at line {line_number}") from error
        if type(row) is not dict or set(row) != {"path", "bytes", "sha256"}:
            raise ValueError(f"invalid manifest fields at line {line_number}")
        name = row["path"]
        if (type(name) is not str or not name or "\\" in name or
                PurePosixPath(name).is_absolute() or
                any(part in ("", ".", "..") for part in name.split("/"))):
            raise ValueError(f"unsafe relative path at line {line_number}")
        if name in seen:
            raise ValueError(f"duplicate path at line {line_number}")
        seen.add(name)
        if (type(row["bytes"]) is not int or row["bytes"] < 0 or
                type(row["sha256"]) is not str or len(row["sha256"]) != 64):
            raise ValueError(f"invalid size or digest at line {line_number}")
        entries.append(row)
        total_bytes += row["bytes"]
    if entries != sorted(entries, key=lambda row: row["path"]):
        raise ValueError("manifest paths are not sorted")
    if total_bytes != readback.get("manifest_total_bytes"):
        raise ValueError("manifest total byte count mismatch")

    for row in entries:
        path = raw_root.joinpath(*row["path"].split("/"))
        try:
            info = path.lstat()
        except FileNotFoundError as error:
            raise ValueError(f"manifest file missing: {row['path']}") from error
        if not stat.S_ISREG(info.st_mode) or path.is_symlink():
            raise ValueError(f"manifest path is not a regular file: {row['path']}")
        if path.resolve(strict=True).parent != raw_root and raw_root not in path.resolve(strict=True).parents:
            raise ValueError(f"manifest path escapes raw root: {row['path']}")
        if info.st_size != row["bytes"] or sha256_file(path) != row["sha256"]:
            raise ValueError(f"manifest content mismatch: {row['path']}")

    listed = {row["path"] for row in entries}
    actual = set()
    for base, dirs, files in os.walk(raw_root, followlinks=False):
        base_path = Path(base)
        for directory in list(dirs):
            if (base_path / directory).is_symlink():
                raise ValueError("symlink directory in raw root")
        for filename in files:
            path = base_path / filename
            actual.add(path.relative_to(raw_root).as_posix())
    if actual != listed:
        raise ValueError("manifest does not enumerate the complete raw root")

    summary_bytes = Path(public_summary_path).read_bytes()
    if sha256_bytes(summary_bytes) != readback.get("public_summary_sha256"):
        raise ValueError("local public summary digest mismatch")
    summary = json.loads(summary_bytes)
    for key in ("allocation", "source_main_sha", "experiment_tree_commit"):
        if summary.get(key) != readback.get(key):
            raise ValueError(f"public summary readback mismatch: {key}")
    for name, expected in readback.get("run_record_sha256", {}).items():
        path = raw_root / name
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"run-record digest mismatch: {name}")

    if public_repo is not None or public_revision is not None:
        if public_repo is None or public_revision is None:
            raise ValueError("both public repo and revision are required")
        tracked = subprocess.check_output(
            ["git", "-C", str(public_repo), "show",
             f"{public_revision}:{readback['public_summary_git_path']}"])
        if sha256_bytes(tracked) != readback["public_summary_sha256"]:
            raise ValueError("tracked public summary does not match local readback")

    return {"status": "PASS_A15_RAW_CUSTODY", "entries": len(entries),
            "total_bytes": total_bytes,
            "manifest_sha256": sha256_bytes(manifest_bytes),
            "public_summary_sha256": readback["public_summary_sha256"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--manifest", default="A15_RAW_SHA256_MANIFEST.jsonl")
    parser.add_argument("--readback", default="A15_CUSTODY_READBACK.json")
    parser.add_argument("--public-summary", required=True)
    parser.add_argument("--public-repo")
    parser.add_argument("--public-revision")
    args = parser.parse_args()
    print(json.dumps(verify(args.raw_root, args.manifest, args.readback,
                            args.public_summary, args.public_repo,
                            args.public_revision), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

"""Compare a retained Calc attempt's runtime manifest with a chosen git ref."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ARCHIVE = Path(
    "research/integration/wslc_calc_partial_input_recovery_20261031"
)
RELEVANT_PARTS = (
    "runtime/backends/win32_v1/",
    "runtime/guarded_win32_v1/",
    "runtime/cli_v1/",
    "runtime/core_v1/",
)


def git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], input=input_bytes
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default="HEAD")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    ref = git(root, "rev-parse", args.ref).decode().strip()
    manifest_path = (ARCHIVE / "runtime-hashes.json").as_posix()
    archive_commit = git(
        root, "log", "-1", "--format=%H", "--", manifest_path
    ).decode().strip()
    pinned = json.loads(git(root, "show", f"{ref}:{manifest_path}"))
    paths = list(pinned)
    batch = git(
        root,
        "cat-file",
        "--batch",
        input_bytes="".join(f"{ref}:{path}\n" for path in paths).encode(),
    )

    matches: list[str] = []
    mismatches: list[str] = []
    missing: list[str] = []
    offset = 0
    for path in paths:
        end = batch.index(b"\n", offset)
        header = batch[offset:end].decode().split()
        offset = end + 1
        if len(header) < 3 or header[1] == "missing":
            missing.append(path)
            continue
        size = int(header[2])
        blob = batch[offset : offset + size]
        offset += size + 1
        target = matches if hashlib.sha256(blob).hexdigest() == pinned[path] else mismatches
        target.append(path)

    relevant = [
        path for path in paths
        if path.startswith(RELEVANT_PARTS) and "/test_" not in path
    ]
    relevant_mismatch = [path for path in mismatches if path in relevant]
    result = {
        "format": "wslc-calc-partial-runtime-lineage-audit-v1",
        "ref": args.ref,
        "ref_commit": ref,
        "archive": str(ARCHIVE),
        "archive_manifest_commit": archive_commit,
        "pinned_runtime_files": len(paths),
        "exact_blob_matches": len(matches),
        "blob_mismatches": len(mismatches),
        "missing_files": missing,
        "relevant_implementation_files": len(relevant),
        "relevant_implementation_mismatches": len(relevant_mismatch),
        "relevant_implementation_mismatch_paths": relevant_mismatch,
        "interpretation": (
            "The archive is bound to a different runtime snapshot. Hash drift alone "
            "does not establish a behavioral regression or current-runtime recovery."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Measure current-main SHA-256 drift against the retained v13 preregistration."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def git_bytes(root: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(root), "show", f"{commit}:{path}"], stderr=subprocess.PIPE
    )


def git_blob_oid(root: Path, commit: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", f"{commit}:{path}"],
        text=True,
        stderr=subprocess.PIPE,
    ).strip()


def run(root: Path, fixture: dict) -> dict:
    commit = fixture["source_commit"]
    prereg_path = fixture["prereg_path"]
    prereg_raw = git_bytes(root, commit, prereg_path)
    prereg = json.loads(prereg_raw)
    expected_maps = {
        "source_sha256": prereg["source_sha256"],
        "canonical_upstream_sha256": prereg["canonical_upstream_sha256"],
    }
    expected: dict[str, set[str]] = {}
    for label, hashes in expected_maps.items():
        if not isinstance(hashes, dict) or not hashes:
            raise ValueError(f"invalid or empty preregistration hash map: {label}")
        for path, digest in hashes.items():
            if not isinstance(path, str) or not path or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                raise ValueError(f"invalid source pin: {label}:{path}")
            expected.setdefault(path, set()).add(digest)

    rows = []
    for path in sorted(expected):
        try:
            source = git_bytes(root, commit, path)
            blob_oid = git_blob_oid(root, commit, path)
            actual = hashlib.sha256(source).hexdigest()
            present = True
        except subprocess.CalledProcessError:
            blob_oid = None
            actual = None
            present = False
        pins = sorted(expected[path])
        rows.append(
            {
                "path": path,
                "expected_sha256": pins,
                "actual_sha256": actual,
                "git_blob_oid": blob_oid,
                "present": present,
                "matches_all_pins": present and len(pins) == 1 and actual == pins[0],
            }
        )

    return {
        "schema": "map01-current-main-source-closure-candidate-v1",
        "source_commit": commit,
        "prereg_path": prereg_path,
        "prereg_blob_oid": git_blob_oid(root, commit, prereg_path),
        "prereg_sha256": hashlib.sha256(prereg_raw).hexdigest(),
        "prereg_allocation_id": prereg.get("allocation_id"),
        "prereg_base_commit": prereg.get("base_commit"),
        "historical_allocation_id": fixture["historical_allocation_id"],
        "expected_source_path_count": len(expected),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("fixture.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    result = run(args.repo_root, fixture)
    serialized = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    args.out.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")


if __name__ == "__main__":
    main()

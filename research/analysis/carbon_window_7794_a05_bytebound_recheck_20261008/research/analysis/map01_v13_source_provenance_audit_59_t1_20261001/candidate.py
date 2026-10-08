"""Hash v13 preregistered sources from exact current-main Git blobs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def git_bytes(root: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{path}"], stderr=subprocess.PIPE)


def collect(root: Path, fixture: dict) -> dict:
    commit, prereg_path = fixture["source_commit"], fixture["prereg_path"]
    raw = git_bytes(root, commit, prereg_path)
    prereg = json.loads(raw)
    pins: dict[str, set[str]] = {}
    for key in ("source_sha256", "canonical_upstream_sha256"):
        mapping = prereg.get(key)
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError(f"invalid or empty preregistration map: {key}")
        for path, digest in mapping.items():
            if not isinstance(path, str) or not path or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                raise ValueError(f"malformed pinned identity: {key}:{path}")
            pins.setdefault(path, set()).add(digest)
    rows = []
    for path, expected_set in sorted(pins.items()):
        try:
            data = git_bytes(root, commit, path)
            blob = subprocess.check_output(["git", "-C", str(root), "rev-parse", f"{commit}:{path}"], text=True, stderr=subprocess.PIPE).strip()
        except subprocess.CalledProcessError:
            data, blob = None, None
        actual = hashlib.sha256(data).hexdigest() if data is not None else None
        expected = sorted(expected_set)
        rows.append({"path": path, "expected_sha256": expected, "actual_sha256": actual,
                     "git_blob_oid": blob, "present": data is not None,
                     "matches_all_pins": data is not None and len(expected) == 1 and actual == expected[0]})
    return {
        "schema": "map01-current-main-source-closure-candidate-v2",
        "source_commit": commit,
        "prereg_path": prereg_path,
        "prereg_blob_oid": subprocess.check_output(["git", "-C", str(root), "rev-parse", f"{commit}:{prereg_path}"], text=True, stderr=subprocess.PIPE).strip(),
        "prereg_sha256": hashlib.sha256(raw).hexdigest(),
        "prereg_allocation_id": prereg.get("allocation_id"),
        "prereg_base_commit": prereg.get("base_commit"),
        "historical_allocation_id": fixture["historical_allocation_id"],
        "expected_source_path_count": len(pins),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("fixture.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.repo_root, json.loads(args.fixture.read_text(encoding="utf-8")))
    raw = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    args.out.write_text(raw, encoding="utf-8", newline="\n")
    print(raw, end="")


if __name__ == "__main__":
    main()

"""Materialize the prior probe's source closure from one immutable Git commit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--prior-manifest", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    package = args.package.resolve()
    prior = json.loads(args.prior_manifest.read_text(encoding="utf-8"))
    files = {}
    for relative in sorted(prior["files"]):
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"unsafe manifest path: {relative}")
        data = subprocess.check_output(
            ["git", "show", f"{args.commit}:{relative}"], cwd=repo)
        target = package / "source-snapshots" / (relative + ".txt")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        files[relative] = {"sha256": hashlib.sha256(data).hexdigest(),
                           "bytes": len(data)}

    manifest = {"ref": args.commit, "files": files}
    (package / "source-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ref": args.commit, "count": len(files),
                      "source_manifest_sha256": hashlib.sha256(
                          (package / "source-manifest.json").read_bytes()).hexdigest()},
                     sort_keys=True))


if __name__ == "__main__":
    main()

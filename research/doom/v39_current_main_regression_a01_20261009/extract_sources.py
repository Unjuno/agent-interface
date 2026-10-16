#!/usr/bin/env python3
"""Extract only the frozen unittest source closure into a temporary directory."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parent
PINS = json.loads((ROOT / "SOURCE_PINS.json").read_text())
parser = argparse.ArgumentParser()
parser.add_argument("--repo", required=True, type=Path)
parser.add_argument("--dest", required=True, type=Path)
args = parser.parse_args()
repo = args.repo.resolve()
dest = args.dest.resolve()
if not repo.is_dir() or not dest.is_dir() or any(dest.iterdir()):
    parser.error("repo must exist and dest must be an existing empty directory")
paths = [item["path"] for item in PINS["source_files"]]
archive = subprocess.run(
    ["git", "-C", str(repo), "archive", PINS["commit"], *paths],
    check=True, stdout=subprocess.PIPE).stdout
with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
    bundle.extractall(dest, filter="data")
print(f"commit={PINS['commit']} unique_files={len(paths)} archive_bytes={len(archive)}")

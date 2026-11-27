#!/usr/bin/env bash
set -euo pipefail
repo="$1"
asset="$2"
mkdir -p "$asset/repo"
cd "$repo"
git archive origin/main runtime | tar -xf - -C "$asset/repo"
printf 'source_commit='
git rev-parse origin/main
printf 'main_archive_runtime_files='
find "$asset/repo/runtime" -type f | wc -l
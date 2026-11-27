#!/bin/sh
set -u
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
mkdir -p results
if [ -e results/candidate.started ] || [ -e results/candidate.raw.json ]; then
  echo "refusing candidate retry or existing output" >&2
  exit 75
fi
printf '%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > results/candidate.started
python3 candidate.py --spec spec.json --output results/candidate.raw.json > results/candidate.stdout.txt 2> results/candidate.stderr.txt
rc=$?
printf '%s\n' "$rc" > results/candidate.exit
if [ -f results/candidate.raw.json ]; then shasum -a 256 results/candidate.raw.json > results/candidate.raw.sha256; fi
exit "$rc"

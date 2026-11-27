#!/bin/sh
set -u
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
mkdir -p results
if [ -e results/auditor.started ] || [ -e results/audit.raw.json ]; then
  echo "refusing auditor retry or existing output" >&2
  exit 75
fi
if [ ! -f results/candidate.exit ] || [ "$(cat results/candidate.exit)" != "0" ] || [ ! -f results/candidate.raw.json ]; then
  echo "candidate gate not satisfied" >&2
  exit 76
fi
printf '%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > results/auditor.started
python3 auditor.py --spec spec.json --raw results/candidate.raw.json --output results/audit.raw.json > results/auditor.stdout.txt 2> results/auditor.stderr.txt
rc=$?
printf '%s\n' "$rc" > results/auditor.exit
if [ -f results/audit.raw.json ]; then shasum -a 256 results/audit.raw.json > results/audit.raw.sha256; fi
exit "$rc"

#!/bin/bash
set -u
cd "$(dirname "$0")/.."
printf 'utc_start=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'kernel=%s\n' "$(uname -a)"
printf 'python=%s\n' "$(python3 --version 2>&1)"
printf 'xvfb=%s\n' "$(Xvfb -version 2>&1 | head -1 || true)"
python3 SOURCE/candidate.py --out results/A01 --cycles 10
candidate_status=$?
if [ -f results/A01/RAW.json ]; then
  python3 SOURCE/audit.py --raw results/A01/RAW.json --freeze FREEZE.json --out results/A01/AUDIT.json
  audit_status=$?
else
  audit_status=125
fi
printf 'candidate_exit=%s\naudit_exit=%s\nutc_end=%s\n' "$candidate_status" "$audit_status" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
exit "$audit_status"

#!/bin/bash
set -u
PACKAGE="$HOME/xlib-query-prefetch-a01"
RESULT=/mnt/diag-results/A01
LOGS=/mnt/diag-results/logs
mkdir -p "$LOGS"
if [ -e "$LOGS/candidate-started" ] || [ -e "$RESULT" ]; then
  echo 'STOP: candidate marker or result exists; refusing invocation' > "$LOGS/refusal.txt"
  exit 90
fi
mkdir -p "$RESULT"
printf 'runner_start=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOGS/runner-time.txt"
cd "$PACKAGE"
python3 -B verify_bundle.py > "$LOGS/preflight.json" 2> "$LOGS/preflight.stderr"
if [ $? -ne 0 ]; then
  echo 'STOP: frozen bundle preflight failed' > "$LOGS/status.txt"
  exit 91
fi
touch "$LOGS/candidate-started"
printf 'candidate_start=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOGS/candidate-time.txt"
python3 -B probe.py > "$RESULT/RAW.json" 2> "$LOGS/candidate.stderr"
candidate_status=$?
printf '%s\n' "$candidate_status" > "$LOGS/candidate.exit"
printf 'candidate_end=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOGS/candidate-time.txt"
if [ "$candidate_status" -eq 0 ] && [ -s "$RESULT/RAW.json" ]; then
  if [ -e "$LOGS/auditor-started" ]; then
    echo 'STOP: auditor marker already exists' > "$LOGS/auditor-refusal.txt"
    exit 92
  fi
  touch "$LOGS/auditor-started"
  python3 -B audit.py --raw "$RESULT/RAW.json" --out "$RESULT/AUDIT.json" > "$LOGS/auditor.stdout" 2> "$LOGS/auditor.stderr"
  audit_status=$?
else
  audit_status=125
fi
printf '%s\n' "$audit_status" > "$LOGS/auditor.exit"
printf 'candidate_exit=%s\nauditor_exit=%s\nrunner_end=%s\n' "$candidate_status" "$audit_status" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOGS/status.txt"
exit "$audit_status"

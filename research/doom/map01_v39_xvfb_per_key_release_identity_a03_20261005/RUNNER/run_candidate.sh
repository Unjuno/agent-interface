#!/bin/bash
set -u
PACKAGE="$HOME/map01-v39-xvfb-a03"
RESULTS=/mnt/a03-results
LOGS="$RESULTS/logs"
mkdir -p "$LOGS"
if [ -e "$LOGS/candidate-started" ] || [ -e "$RESULTS/A03" ]; then
  echo 'STOP: candidate marker or result exists; refusing invocation' | tee "$LOGS/refusal.txt"
  exit 90
fi
cd "$PACKAGE"
python3 RUNNER/verify_bundle.py > "$LOGS/preflight.json" 2> "$LOGS/preflight.stderr"
if [ $? -ne 0 ]; then
  echo 'STOP: frozen bundle preflight failed' > "$LOGS/status.txt"
  exit 91
fi
python3 -B RUNNER/focus_smoke.py > "$LOGS/focus-smoke.json" 2> "$LOGS/focus-smoke.stderr"
if [ $? -ne 0 ]; then
  echo 'STOP: isolated focus smoke failed; candidate not invoked' > "$LOGS/status.txt"
  exit 93
fi
touch "$LOGS/candidate-started"
printf 'candidate_start=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOGS/candidate-time.txt"
python3 -B SOURCE/candidate.py --out "$RESULTS/A03" --cycles 10 > "$LOGS/candidate.stdout" 2> "$LOGS/candidate.stderr"
candidate_status=$?
printf '%s\n' "$candidate_status" > "$LOGS/candidate.exit"
printf 'candidate_end=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOGS/candidate-time.txt"
if [ -f "$RESULTS/A03/RAW.json" ]; then
  if [ -e "$LOGS/auditor-started" ]; then
    echo 'STOP: auditor marker already exists' > "$LOGS/auditor-refusal.txt"
    exit 92
  fi
  touch "$LOGS/auditor-started"
  python3 -B SOURCE/audit.py --raw "$RESULTS/A03/RAW.json" --freeze FREEZE.json --out "$RESULTS/A03/AUDIT.json" > "$LOGS/auditor.stdout" 2> "$LOGS/auditor.stderr"
  audit_status=$?
else
  audit_status=125
fi
printf '%s\n' "$audit_status" > "$LOGS/auditor.exit"
printf 'candidate_exit=%s\nauditor_exit=%s\nrunner_end=%s\n' "$candidate_status" "$audit_status" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOGS/status.txt"
exit "$audit_status"

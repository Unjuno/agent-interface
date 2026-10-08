#!/bin/sh
set -u
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel) || exit 90
expected_pkg="$repo_root/research/analysis/anchoring_vignette_identifiability_8522_t0_a02_20261009"
if [ "$script_dir" != "$expected_pkg" ]; then
  printf '%s\n' "STOP: unexpected package location: $script_dir" >&2
  exit 91
fi
out="$script_dir/results/formal-02"
if [ -e "$out/RUN_STARTED" ]; then
  printf '%s\n' "STOP: formal allocation already started; retries are forbidden" >&2
  exit 92
fi
mkdir -p "$out" || exit 93
touch "$out/RUN_STARTED" || exit 94
python3.12 --version > "$out/python.version" 2>&1
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$out/candidate.start.utc"
python3.12 "$script_dir/candidate.py" "$script_dir/candidate_input.json" "$out/candidate.json" > "$out/candidate.stdout" 2> "$out/candidate.stderr"
candidate_rc=$?
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$out/candidate.end.utc"
printf '%s\n' "$candidate_rc" > "$out/candidate.exit"
if [ "$candidate_rc" -ne 0 ] || [ ! -s "$out/candidate.json" ]; then
  printf '%s\n' 'NOT_RUN' > "$out/auditor.invocation"
  printf 'candidate_rc=%s auditor=NOT_RUN\n' "$candidate_rc" > "$out/exit_summary.txt"
  exit 0
fi
printf '%s\n' '1' > "$out/auditor.invocation"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$out/auditor.start.utc"
python3.12 "$script_dir/auditor.py" "$script_dir/candidate_input.json" "$out/candidate.json" "$script_dir/oracle.json" "$out/audit.json" > "$out/auditor.stdout" 2> "$out/auditor.stderr"
auditor_rc=$?
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$out/auditor.end.utc"
printf '%s\n' "$auditor_rc" > "$out/auditor.exit"
printf 'candidate_rc=%s auditor_rc=%s\n' "$candidate_rc" "$auditor_rc" > "$out/exit_summary.txt"
exit 0

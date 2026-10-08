#!/usr/bin/env bash
set -u

PKG="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
OUT="$PKG/results/allocation-01"
IMAGE='python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
started_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ -e "$OUT" ]]; then
  printf 'STOP: allocation output already exists: %s\n' "$OUT" >&2
  exit 73
fi

mkdir -p "$OUT/candidate" "$OUT/audit"
uid="$(id -u)"
gid="$(id -g)"

candidate=(docker --context orbstack run --pull=never --rm --platform linux/arm64
  --network none --cpus=1 --memory=536870912 --pids-limit=64 --read-only
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop=ALL
  --security-opt no-new-privileges --user "$uid:$gid"
  --mount "type=bind,source=$PKG,target=/src,readonly"
  --mount "type=bind,source=$OUT/candidate,target=/out"
  --workdir /src --cidfile "$OUT/candidate.cid" "$IMAGE"
  python -B candidate.py scenarios.json /out/candidate.json)

auditor=(docker --context orbstack run --pull=never --rm --platform linux/arm64
  --network none --cpus=1 --memory=536870912 --pids-limit=64 --read-only
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop=ALL
  --security-opt no-new-privileges --user "$uid:$gid"
  --mount "type=bind,source=$PKG,target=/src,readonly"
  --mount "type=bind,source=$OUT/candidate,target=/candidate,readonly"
  --mount "type=bind,source=$OUT/audit,target=/out"
  --workdir /src --cidfile "$OUT/auditor.cid" "$IMAGE"
  python -B auditor.py scenarios.json /candidate/candidate.json /out/audit.json)

printf '%q ' "${candidate[@]}" > "$OUT/candidate.command.txt"
printf '\n' >> "$OUT/candidate.command.txt"
printf '%q ' "${auditor[@]}" > "$OUT/auditor.command.txt"
printf '\n' >> "$OUT/auditor.command.txt"

set +e
"${candidate[@]}" > "$OUT/candidate.stdout.txt" 2> "$OUT/candidate.stderr.txt"
candidate_rc=$?
printf '%s\n' "$candidate_rc" > "$OUT/candidate.exit"

"${auditor[@]}" > "$OUT/auditor.stdout.txt" 2> "$OUT/auditor.stderr.txt"
auditor_rc=$?
printf '%s\n' "$auditor_rc" > "$OUT/auditor.exit"
set -e

python -B "$PKG/record_run.py" "$OUT" "$candidate_rc" "$auditor_rc" "$started_utc"
printf 'candidate_exit=%s auditor_exit=%s\n' "$candidate_rc" "$auditor_rc"
if [[ "$candidate_rc" -ne 0 || "$auditor_rc" -ne 0 ]]; then
  exit 1
fi

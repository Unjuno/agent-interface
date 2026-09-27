#!/bin/sh
set -eu

ROOT=${1:?repository root required}
EVIDENCE=${2:?formal evidence path required}
OUT=${3:?fresh audit output path required}
LOG=${4:?separate host log path required}
IMAGE=python:3.12-slim-bookworm
EXPECTED_ID=sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
STUDY="$ROOT/research/integration/broker_fake_child_boundary_4485_orbstack_successor_v1"

test "$(docker context show)" = orbstack || { echo STOP_DOCKER_CONTEXT; exit 64; }
test "$(docker image inspect "$IMAGE" --format '{{.Id}}')" = "$EXPECTED_ID" || { echo STOP_IMAGE_ID; exit 64; }
test "$(docker image inspect "$IMAGE" --format '{{.Os}}/{{.Architecture}}')" = linux/arm64 || { echo STOP_IMAGE_PLATFORM; exit 64; }
test -s "$EVIDENCE/RESULT.json" || { echo STOP_RAW_MISSING; exit 64; }
if [ -e "$OUT" ] && [ -n "$(find "$OUT" -mindepth 1 -print -quit)" ]; then
  echo STOP_AUDIT_OUTPUT_NOT_EMPTY
  exit 64
fi
mkdir -p "$OUT" "$LOG"

set +e
docker run --rm --pull=never --platform=linux/arm64 --network=none --read-only \
  --name issue5037-broker-audit-01 \
  --security-opt=no-new-privileges --cap-drop=ALL \
  --cpus=0.25 --memory=512m --memory-swap=512m --pids-limit=32 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m \
  -v "$STUDY:/src:ro" -v "$EVIDENCE:/evidence:ro" -v "$OUT:/audit:rw" \
  -w /src "$IMAGE" python -B /src/audit_raw.py \
  /evidence/RESULT.json /src/FREEZE.json \
  >"$OUT/AUDIT.json" 2>"$LOG/audit.stderr.txt"
rc=$?
set -e
printf '%s\n' "$rc" > "$LOG/audit.exit"
exit "$rc"

#!/bin/sh
set -eu

ROOT=${1:?repository root required}
OUT=${2:?fresh formal output path required}
LOG=${3:?separate host log path required}
IMAGE=python:3.12-slim-bookworm
EXPECTED_ID=sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
STUDY="$ROOT/research/integration/broker_fake_child_boundary_4485_orbstack_successor_v1"

test "$(docker context show)" = orbstack || { echo STOP_DOCKER_CONTEXT; exit 64; }
test "$(docker image inspect "$IMAGE" --format '{{.Id}}')" = "$EXPECTED_ID" || { echo STOP_IMAGE_ID; exit 64; }
test "$(docker image inspect "$IMAGE" --format '{{.Os}}/{{.Architecture}}')" = linux/arm64 || { echo STOP_IMAGE_PLATFORM; exit 64; }
if [ -e "$OUT" ] && [ -n "$(find "$OUT" -mindepth 1 -print -quit)" ]; then
  echo STOP_OUTPUT_NOT_EMPTY
  exit 64
fi
mkdir -p "$OUT" "$LOG"

set +e
docker run --rm --pull=never --platform=linux/arm64 --network=none --read-only \
  --name issue5037-broker-formal-01 \
  --security-opt=no-new-privileges --cap-drop=ALL \
  --cpus=0.25 --memory=512m --memory-swap=512m --pids-limit=32 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=32m \
  --tmpfs /fakeexec:rw,exec,nosuid,nodev,size=16m \
  -v "$ROOT:/repo:ro" -v "$STUDY:/src:ro" -v "$OUT:/out:rw" \
  -w /repo "$IMAGE" python -B /src/run_cases.py \
  >"$LOG/formal.stdout.txt" 2>"$LOG/formal.stderr.txt"
rc=$?
set -e
printf '%s\n' "$rc" > "$LOG/formal.exit"
exit "$rc"

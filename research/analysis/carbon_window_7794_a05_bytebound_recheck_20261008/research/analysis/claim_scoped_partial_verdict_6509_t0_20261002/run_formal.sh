#!/bin/sh
set -u

SRC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT_DIR="$SRC_DIR/results/allocation-01"
IMAGE='python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
UID_VALUE=$(id -u)
GID_VALUE=$(id -g)

if [ -e "$OUT_DIR" ]; then
    printf '%s\n' 'STOP_OUTPUT_PATH_ALREADY_EXISTS' >&2
    exit 73
fi
mkdir -p "$OUT_DIR/audit"

docker run --rm --cidfile "$OUT_DIR/candidate.cid" \
    --network none --cpus 0.25 --memory 512m --pids-limit 32 \
    --read-only --tmpfs /tmp:rw,nosuid,size=64m \
    --cap-drop ALL --security-opt no-new-privileges \
    --user "$UID_VALUE:$GID_VALUE" \
    --mount "type=bind,src=$SRC_DIR/candidate.py,dst=/src/candidate.py,readonly" \
    --mount "type=bind,src=$SRC_DIR/scenarios.json,dst=/src/scenarios.json,readonly" \
    --mount "type=bind,src=$OUT_DIR,dst=/out" \
    --entrypoint python "$IMAGE" /src/candidate.py /src/scenarios.json /out/candidate.json \
    >"$OUT_DIR/candidate.stdout.txt" 2>"$OUT_DIR/candidate.stderr.txt"
CANDIDATE_EXIT=$?
printf '%s\n' "$CANDIDATE_EXIT" >"$OUT_DIR/candidate.exit"
if [ "$CANDIDATE_EXIT" -ne 0 ]; then
    exit "$CANDIDATE_EXIT"
fi

docker run --rm --cidfile "$OUT_DIR/audit/auditor.cid" \
    --network none --cpus 0.25 --memory 512m --pids-limit 32 \
    --read-only --tmpfs /tmp:rw,nosuid,size=64m \
    --cap-drop ALL --security-opt no-new-privileges \
    --user "$UID_VALUE:$GID_VALUE" \
    --mount "type=bind,src=$SRC_DIR/audit.py,dst=/src/audit.py,readonly" \
    --mount "type=bind,src=$SRC_DIR/scenarios.json,dst=/src/scenarios.json,readonly" \
    --mount "type=bind,src=$OUT_DIR/candidate.json,dst=/raw/candidate.json,readonly" \
    --mount "type=bind,src=$OUT_DIR/audit,dst=/auditout" \
    --entrypoint python "$IMAGE" /src/audit.py /src/scenarios.json /raw/candidate.json /auditout/audit.json \
    >"$OUT_DIR/audit/auditor.stdout.txt" 2>"$OUT_DIR/audit/auditor.stderr.txt"
AUDITOR_EXIT=$?
printf '%s\n' "$AUDITOR_EXIT" >"$OUT_DIR/audit/auditor.exit"
exit "$AUDITOR_EXIT"

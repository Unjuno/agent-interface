#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
IMAGE=python:3.12-slim
EXPECTED=sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
ACTUAL=$(docker image inspect "$IMAGE" --format '{{.Id}}')
[ "$ACTUAL" = "$EXPECTED" ] || { echo "STOP: image id mismatch: $ACTUAL" >&2; exit 12; }
OUT="$ROOT/run"
mkdir -p "$OUT"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/started_at.txt"
printf '%s\n' "$ACTUAL" > "$OUT/image_id.txt"
docker run --rm --network none --cpus=1 --memory=256m --pids-limit=64 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop=ALL --security-opt=no-new-privileges \
  -v "$ROOT/input:/input:ro" -v "$ROOT:/work:ro" -v "$OUT:/out:rw" -w /work "$IMAGE" \
  python candidate.py /input/cases.json > "$OUT/candidate.json"
docker run --rm --network none --cpus=1 --memory=256m --pids-limit=64 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop=ALL --security-opt=no-new-privileges \
  -v "$ROOT/input:/input:ro" -v "$ROOT:/work:ro" -v "$OUT:/out:ro" -w /work "$IMAGE" \
  python auditor.py /input/cases.json /work/oracle.json /out/candidate.json > "$OUT/audit.json"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/completed_at.txt"
(cd "$ROOT" && find run -maxdepth 1 -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > run/SHA256SUMS)

#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
IMAGE=python:3.12-slim
EXPECTED=sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
ACTUAL=$(docker image inspect "$IMAGE" --format '{{.Id}}')
[ "$ACTUAL" = "$EXPECTED" ] || { echo "STOP image identity mismatch: $ACTUAL" >&2; exit 12; }
OUT="$ROOT/run"
mkdir -p "$OUT"
for name in candidate.json audit.json; do
  [ ! -e "$OUT/$name" ] || { echo "STOP formal artifact already exists: $name" >&2; exit 13; }
done
printf '%s\n' "$ACTUAL" > "$OUT/image_id.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/candidate_started_at.txt"
docker run --rm --network none --cpus=1 --memory=256m --pids-limit=64 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop=ALL --security-opt=no-new-privileges \
  -v "$ROOT:/work:ro" -w /work "$IMAGE" python candidate.py /work/fixture.json > "$OUT/candidate.json"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/candidate_completed_at.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/auditor_started_at.txt"
docker run --rm --network none --cpus=1 --memory=256m --pids-limit=64 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop=ALL --security-opt=no-new-privileges \
  -v "$ROOT:/work:ro" -w /work "$IMAGE" python auditor.py /work/fixture.json /work/run/candidate.json > "$OUT/audit.json"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/auditor_completed_at.txt"
python -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["decision"]); sys.exit(0 if d["decision"]=="METHOD_PASS_SCOPED" else 1)' "$OUT/audit.json"
(cd "$ROOT" && find run -maxdepth 1 -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > run/SHA256SUMS)

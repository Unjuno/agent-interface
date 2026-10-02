#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
IMAGE=python:3.12-slim
EXPECTED=sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
OUT="$ROOT/formal"
ACTUAL=$(docker image inspect "$IMAGE" --format '{{.Id}}')
[ "$ACTUAL" = "$EXPECTED" ] || { echo "STOP_INFRA image mismatch: $ACTUAL" >&2; exit 70; }
[ ! -e "$OUT" ] || { echo "STOP_INFRA output already exists" >&2; exit 71; }
mkdir "$OUT"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/start_utc.txt"

docker run --rm --network none --cpus 1 --memory 512m --pids-limit 64 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$ROOT/candidate.py,dst=/candidate.py,readonly" \
  --mount "type=bind,src=$ROOT/fixture.json,dst=/fixture.json,readonly" \
  --entrypoint python "$IMAGE" /candidate.py /fixture.json > "$OUT/candidate.stdout.json" 2> "$OUT/candidate.stderr.txt" || {
    rc=$?; echo "$rc" > "$OUT/candidate.exit_code.txt"; echo "STOP_INFRA candidate exit $rc" > "$OUT/status.txt"; exit "$rc";
  }
echo 0 > "$OUT/candidate.exit_code.txt"

docker run --rm --network none --cpus 1 --memory 512m --pids-limit 64 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$ROOT/auditor.py,dst=/auditor.py,readonly" \
  --mount "type=bind,src=$ROOT/fixture.json,dst=/fixture.json,readonly" \
  --mount "type=bind,src=$ROOT/oracle.json,dst=/oracle.json,readonly" \
  --mount "type=bind,src=$OUT/candidate.stdout.json,dst=/candidate.json,readonly" \
  --entrypoint python "$IMAGE" /auditor.py /fixture.json /oracle.json /candidate.json > "$OUT/audit.stdout.json" 2> "$OUT/audit.stderr.txt" || {
    rc=$?; echo "$rc" > "$OUT/auditor.exit_code.txt"; echo "STOP_INFRA auditor exit $rc" > "$OUT/status.txt"; exit "$rc";
  }
echo 0 > "$OUT/auditor.exit_code.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/end_utc.txt"
python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); print(x["status"])' "$OUT/audit.stdout.json" > "$OUT/status.txt"
shasum -a 256 "$ROOT/fixture.json" "$ROOT/oracle.json" "$ROOT/candidate.py" "$ROOT/auditor.py" "$OUT/candidate.stdout.json" "$OUT/audit.stdout.json" > "$OUT/SHA256SUMS.txt"

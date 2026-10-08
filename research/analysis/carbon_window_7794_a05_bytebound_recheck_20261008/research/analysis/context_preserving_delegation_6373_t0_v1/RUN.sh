#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
IMAGE=python:3.12-slim
docker image inspect "$IMAGE" --format '{{.Id}}' > "$ROOT/image-id.txt"
docker run --rm --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges \
  -v "$ROOT:/work:ro" -w /work "$IMAGE" python -B candidate.py input/cases.json > "$ROOT/candidate.json"
cp "$ROOT/input/cases.json" "$ROOT/raw.json"
docker run --rm --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges \
  -v "$ROOT:/work:ro" -w /work "$IMAGE" python -B auditor.py raw.json oracle.json candidate.json > "$ROOT/audit.json"
date -u +%FT%TZ > "$ROOT/executed-at-utc.txt"
sha256sum "$ROOT/PREREG.md" "$ROOT/candidate.py" "$ROOT/auditor.py" "$ROOT/build_check.py" "$ROOT/RUN.sh" "$ROOT/input/cases.json" "$ROOT/oracle.json" "$ROOT/raw.json" "$ROOT/candidate.json" "$ROOT/audit.json" > "$ROOT/SHA256SUMS"

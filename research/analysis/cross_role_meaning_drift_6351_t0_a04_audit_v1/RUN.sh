#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
IMAGE=python:3.12-slim
docker image inspect "$IMAGE" --format '{{.Id}}' > "$ROOT/image-id.txt"
docker run --rm --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges \
  -v "$ROOT:/work:ro" -w /work "$IMAGE" python -B auditor.py input/raw.json input/candidate.json input/oracle.json > "$ROOT/audit.json"
date -u +%FT%TZ > "$ROOT/executed-at-utc.txt"
sha256sum "$ROOT/auditor.py" "$ROOT/build_check.py" "$ROOT/PREREG.md" "$ROOT/input/raw.json" "$ROOT/input/candidate.json" "$ROOT/input/oracle.json" "$ROOT/audit.json" > "$ROOT/SHA256SUMS"

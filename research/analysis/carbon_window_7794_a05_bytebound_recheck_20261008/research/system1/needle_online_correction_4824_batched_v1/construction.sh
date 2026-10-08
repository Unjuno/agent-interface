#!/usr/bin/env sh
set -eu
docker run --rm --pull=never --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=512m --memory=2g --cpus=1 \
  --pids-limit=64 --security-opt=no-new-privileges \
  -e PYTHONPYCACHEPREFIX=/tmp/pycache \
  -v "$PWD":/src:ro -v needle-online-correction-4824-batched-construction-v1:/out:rw \
  --entrypoint python3 needle-pilot05:local /src/runner.py
docker run --rm --pull=never --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=512m --memory=2g --cpus=1 \
  --pids-limit=64 --security-opt=no-new-privileges \
  -e PYTHONPYCACHEPREFIX=/tmp/pycache \
  -v "$PWD":/src:ro -v needle-online-correction-4824-batched-construction-v1:/out:ro \
  --entrypoint python3 needle-pilot05:local /src/audit.py /out/construction/raw.json


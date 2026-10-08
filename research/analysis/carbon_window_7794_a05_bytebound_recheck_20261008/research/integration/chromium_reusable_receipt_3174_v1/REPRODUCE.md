# Reproduction command
docker run --rm --network none -w /work \
  -v <frozen-source>:/work:ro -v <writable-results>:/work/results \
  --entrypoint python3 python:3.12-slim-bookworm /work/src/formal_runner.py

docker run --rm --network none -w /work \
  -v <frozen-source>:/work:ro -v <writable-results>:/work/results \
  --entrypoint python3 python:3.12-slim-bookworm /work/src/audit.py

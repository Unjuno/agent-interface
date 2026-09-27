# Reproduction commands

Run from macOS with OrbStack Docker context and the pinned image already available locally.

```sh
docker --context orbstack image inspect python:3.12-slim --format '{{.Id}} {{.Os}}/{{.Architecture}}'
docker --context orbstack run --rm --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  -v "$PWD/source:/work/source:ro" \
  -v "$PWD/runner.py:/work/runner.py:ro" \
  -v "$PWD/results/construction-final-03:/work/out:rw" \
  -e OBSTAC_SOURCE_COMMIT=4d51fccac55433570bc714cfaf21c88531fe325d \
  -e OBSTAC_SOURCE_TREE=7fae16c1766a36376d6c49f49a7fb0e68f93cb0d \
  -e OBSTAC_IMAGE_ID=sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  -e OBSTAC_FREEZE_SHA256=15af12fe44fd33d269ce42a485cd0d6b6c9e94070a4dd633bca0cc543f0629a5 \
  -e OBSTAC_DOCKER_CONTEXT=orbstack -e OBSTAC_PLATFORM=linux/arm64 \
  -e OBSTAC_RUN_KIND=construction \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python -B /work/runner.py
```

Formal execution uses the identical arguments but a newly created empty
`results/formal-01/` output directory and `OBSTAC_RUN_KIND=formal`. This command
is run exactly once after the frozen bundle is published; no retry is allowed.
The independent audit uses a separate invocation of the same image with
`audit.py`, `source` and the formal `raw.json` mounted read-only, a dedicated
audit output mount, and `--network none --read-only`.

`construction-01/` and `construction-final-02/` retain two setup STOPs; the
successful construction dataset is `construction-final-03/construction.json`.

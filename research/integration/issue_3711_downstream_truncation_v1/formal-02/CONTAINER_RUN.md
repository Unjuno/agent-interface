# Container run record — allocation 02

Both commands ran through OrbStack Docker 29.4.0 on `linux/arm64`, using the digest-pinned image in `successor-02/FREEZE.json`, with `--network none`, `--read-only`, source mounted read-only, `--cap-drop ALL`, `no-new-privileges`, and a bounded tmpfs. The runner's result directory was the only writable bind mount. The independent auditor ran in a second fresh container.

Runner command (from repository root; use a new empty output directory only for a newly identified allocation):

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,exec,size=64m --pids-limit 32 --memory 512m --cpus 1 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD",target=/src,readonly \
  --mount type=bind,source="$PWD/research/integration/issue_3711_downstream_truncation_v1/formal-02",target=/out \
  --env SOURCE_ROOT=/src --env ENGINE_PLATFORM=linux/arm64 \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /src/research/integration/issue_3711_downstream_truncation_v1/successor-02/experiment.py /out
```

The runner exited 0 and printed `write_return_values:[246]`, `delivered_bytes:23`, consumer `JSONDecodeError`, and `dispatch_calls_after_recovery:1`.

Independent audit command (separate fresh container, same image/security boundary):

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,exec,size=64m --pids-limit 16 --memory 256m --cpus 1 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source="$PWD",target=/src,readonly \
  --mount type=bind,source="$PWD/research/integration/issue_3711_downstream_truncation_v1/formal-02",target=/out \
  --env SOURCE_ROOT=/src \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python /src/research/integration/issue_3711_downstream_truncation_v1/successor-02/audit.py /out /src
```

Audit exited 0: `PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY`, errors `[]`. It wrote `audit.json`; the other result files' SHA-256 values were checked afterward and match the independent audit's raw/request/report hashes.

These are reproduction instructions, not permission to reuse allocation 02. Any repeat must receive a new allocation identity, freeze, output path, and Issue preregistration.

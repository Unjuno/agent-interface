# Allocation 01 construction STOP

Disposition: `STOP_CONSTRUCTION_HARNESS_IMPORT`. The frozen test command did
not import `test_lifecycle.py`, so no retained prediction parity check ran and
no formal comparison or independent audit was launched.

## Invocation and output

- Allocation: `needle-role-skill-lifecycle-4916-v2-20260928-01`
- Freeze commit: `c7556708c749469fca9ae1a0ea132786761afcfd`
- Pinned image: `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`
- Platform/runtime observed in container: linux/amd64, CPython 3.13.5,
  `x86_64`, OrbStack Linux kernel `7.0.14-orbstack-00380-ga7e0a2dc9535`
- Docker limits: network none, read-only root and source, 0.25 CPU, 512 MiB,
  32 PIDs; zero retries.
- Docker exit: 1; unittest discovered 1 failed import, 0 assertion failures.
- Raw receipt: `results/construction-01/construction.json`, SHA-256
  `f0793de709dc0dc18d82e34675eb46bf18b667c3c3e5bb5aad6e9331f31cf2cc`.

Exact invocation:

```sh
docker run --rm --pull=never --platform linux/amd64 --network none \
  --cpus=0.25 --memory=512m --pids-limit=32 --read-only \
  --env ROLE_SKILL_DATA_DIR=/inputs --env OUT_DIR=/out \
  --mount type=bind,source=<study-directory>,target=/src,readonly \
  --mount type=bind,source=<seed-3788-builder-directory>,target=/inputs,readonly \
  --mount type=bind,source=<construction-01-output>,target=/out \
  --entrypoint python \
  sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419 \
  -B /src/construction_runner.py
```

The error is a harness-path defect, not a result about role-skill predictions
or lifecycle cost. `os.environ.get("ROLE_SKILL_DATA_DIR", fallback)` evaluated
`fallback` eagerly; because `/src` has no repository parents, `ROOT.parents[1]`
raised `IndexError` even though the environment variable was supplied. The
frozen source is left unchanged. Formal invocation count is 0/1. No model was
loaded, no fit/optimizer update or prediction was performed, and no timing
result is inferred. A successor must use a fresh Issue/allocation/branch/path,
fix path selection before freezing, and repeat the parity construction gate;
allocation 01 must never be retried.

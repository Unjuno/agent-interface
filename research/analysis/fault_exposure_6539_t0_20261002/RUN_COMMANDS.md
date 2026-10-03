# Issue #6539 WSLc run commands — frozen-candidate draft

Run in PowerShell only after GitHub records an explicit non-overlapping
allocation to Issue #6539 and the start gate in `FREEZE.json` passes. These
commands use Microsoft's native WSL Containers `wslc.exe`; they do not use
Docker Desktop, Podman, or a repository CI container. Never pull an image.

## Fixed runtime

- Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- Local image ID: `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`
- Platform/Python: `linux/amd64`, CPython 3.12.14
- WSLc options: `--pull never --network none --cpus 0.25 --memory 512m --user 65534:65534`
- Source bind is read-only; per-invocation output bind is new and writable.
- WSLc does not expose a rootfs read-only option; retain this runtime limitation.
- If WSLc emits cgroup/swap warnings, preserve them and do not claim effective
  memory or swap enforcement beyond observed evidence.

## Prepare paths (no execution)

Set `$SRC` to the absolute path of this exact study directory, `$CANDIDATE_OUT`
to `$SRC/formal_01_20261002/candidate_out`, and `$AUDIT_OUT` to
`$SRC/formal_01_20261002/audit_out`. Verify the directories do not exist and
the source directory contains the hashes in `FREEZE.json`. Do not reuse a
construction host-output directory.

## Candidate (one invocation only)

```powershell
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 `
  --mount "type=bind,source=$SRC,target=/src,readonly" `
  --mount "type=bind,source=$CANDIDATE_OUT,target=/out" `
  -w /src --entrypoint python `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  -B candidate.py --out /out/candidate.raw.json
```

Preserve complete stdout/stderr, exit status, container inspect metadata, and
host input/output hashes. Do not continue to auditor unless candidate exits 0
and exactly one raw file exists.

## Auditor (one separate invocation, only after candidate exit 0)

Use `$AUDIT_OUT` and mount candidate output read-only at `$CANDIDATE_OUT`.

```powershell
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 `
  --mount "type=bind,source=$SRC,target=/src,readonly" `
  --mount "type=bind,source=$CANDIDATE_OUT,target=/results,readonly" `
  --mount "type=bind,source=$AUDIT_OUT,target=/out" `
  -w /src --entrypoint python `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  -B auditor.py --raw /results/candidate.raw.json --out /out/audit.json
```

Maximum invocations: one candidate and one auditor, retries zero. Any failed
start gate or first invocation outcome is preserved as STOP; do not launch a
replacement, change seeds, or edit thresholds.

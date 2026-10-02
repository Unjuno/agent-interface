# Reproduction

This is a synthetic method check. Run the candidate once and the independent raw-only auditor once, in separate containers, with the pinned image and limits below. Do not reuse the formal output directory for another candidate invocation.

```powershell
$p = (Resolve-Path 'scratch/issue5760-route-assignment-t0-20261001').Path
$out = Join-Path $p 'outputs/formal01'
New-Item -ItemType Directory -Path $out
docker run --rm --network none --cpus=1 --memory=256m --pids-limit=64 `
  --mount "type=bind,source=$p,target=/work,readonly" `
  --mount "type=bind,source=$out,target=/out" --workdir /work `
  python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python runner.py

$raw = (Resolve-Path (Join-Path $out 'raw.json')).Path
docker run --rm --network none --cpus=1 --memory=256m --pids-limit=64 `
  --mount "type=bind,source=$raw,target=/in/raw.json,readonly" `
  --mount "type=bind,source=$p,target=/work,readonly" --workdir /work `
  python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python audit.py /in/raw.json
```

The retained allocation was actually executed once for each command. `REPORT.md` and `outputs/formal01/execution.json` contain the executed result and hashes. The construction-only preflight is not a substitute for these formal invocations.

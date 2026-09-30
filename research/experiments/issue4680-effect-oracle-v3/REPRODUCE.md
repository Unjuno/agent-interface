# Reproduction

From a fresh checkout of this PR's `main` branch, run from the repository root in PowerShell. Choose a new, empty writable output directory outside the read-only source mount; do not reuse the committed `outputs/` evidence directory:

```powershell
$experiments=(Resolve-Path 'research\experiments').Path
$src=Join-Path $experiments 'issue4680-effect-oracle-v3'
$out=Join-Path $env:TEMP 'issue4680-effect-oracle-v3-reproduction-output'
if (Test-Path -LiteralPath $out) { throw "Choose a fresh output directory: $out" }
New-Item -ItemType Directory -Path $out | Out-Null
docker run --rm --network none --cpus 1 --memory 128m --pids-limit 16 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --security-opt no-new-privileges --cap-drop ALL --mount "type=bind,source=$experiments,target=/work,readonly" --mount "type=bind,source=$out,target=/out" --entrypoint python python:3.11-slim -B /work/issue4680-effect-oracle-v3/execute.py /out /work/issue4680-skillpackage-construction
```

The cached image identity and all source/input hashes are frozen in `FREEZE.json`. This audits retained data; it does not rerun the prior proposer, allocator, or auditor. Do not reuse the consumed allocation or overwrite committed raw outputs. Use a separate disposable checkout/output directory for any reproduction.


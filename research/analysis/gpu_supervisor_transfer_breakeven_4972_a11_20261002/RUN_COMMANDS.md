# Allocation 11 — one-shot WSLc commands

Run only after the allocation 11 is recorded prospectively in #5085 and its bounded RTX 3080 window is owner-confirmed, #5085 conflicts/releases are refreshed, all start gates pass, and the exact main/source/image/data identities are rechecked. Never retry within this allocation.

PowerShell from the repository checkout (paths are illustrative but must be recorded exactly):

```powershell
$image = 'pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067'
$study = (Resolve-Path '.\research\analysis\gpu_supervisor_transfer_breakeven_4972_a11_20261002').Path
$out = Join-Path (Get-Location) 'research\outputs\gpu_supervisor_transfer_breakeven_4972_a11_20261002'
if (Test-Path $out) { throw 'STOP_OUTPUT_EXISTS' }
New-Item -ItemType Directory -Path $out | Out-Null
wslc.exe run --rm --pull=never --network none --cpus 2 --memory 2g --gpus all --tmpfs /tmp:rw,nosuid,nodev,size=64m --env AI_IMAGE_REF=$image --env AI_OUTPUT_DIR=/out --mount "type=bind,source=$study,target=/study,readonly" --mount "type=bind,source=$out,target=/out" --workdir /study --entrypoint python $image runner.py *> (Join-Path $out 'candidate.combined.log')
$candidateExit = $LASTEXITCODE
Set-Content -NoNewline (Join-Path $out 'candidate.exit.txt') $candidateExit
```

Proceed only if candidate exit is 0 and exactly one candidate_result.json exists. Then run one independent raw-only CPU audit with no GPU:

```powershell
wslc.exe run --rm --pull=never --network none --cpus 1 --memory 1g --tmpfs /tmp:rw,nosuid,nodev,size=32m --env AI_IMAGE_REF=$image --env AI_CANDIDATE_PATH=/out/candidate_result.json --env AI_OUTPUT_DIR=/out --mount "type=bind,source=$study,target=/study,readonly" --mount "type=bind,source=$out,target=/out" --workdir /study --entrypoint python $image audit.py *> (Join-Path $out 'auditor.combined.log')
$auditorExit = $LASTEXITCODE
Set-Content -NoNewline (Join-Path $out 'auditor.exit.txt') $auditorExit
```

Capture separate stdout/stderr if WSLc provides streams separately; otherwise retain the exact combined stream. Candidate and auditor have independent one-invocation ceilings; retry budget is zero. Confirm output names and hashes after each process. Record WSLc’s actual resource/cgroup/swap observations. Do not describe read-only root or PID enforcement: WSLc CLI does not expose those controls.

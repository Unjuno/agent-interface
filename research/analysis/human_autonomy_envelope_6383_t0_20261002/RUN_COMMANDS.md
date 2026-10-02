# WSLc T0 invocation commands

Run from a clean PowerShell prompt at repository root after verifying `FREEZE.json` source hashes, current `HEAD`, the pinned image, an absent output path, and current WSLc/process/GPU inventory. Preserve the exact raw stdout/stderr and exit code. The candidate and auditor each run at most once; retry budget is zero.

```powershell
$image = 'pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067'
$root = (Resolve-Path '.').Path
$study = Join-Path $root 'research\analysis\human_autonomy_envelope_6383_t0_20261002'
$out = Join-Path $root 'research\outputs\human_autonomy_envelope_6383_t0_20261002_a02'
if (Test-Path $out) { throw 'STOP_OUTPUT_PATH_EXISTS' }
New-Item -ItemType Directory -Path $out | Out-Null

wslc.exe run --rm --pull=never --network none --cpus 1 --memory 1g --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,source=$study,target=/study,readonly" --mount "type=bind,source=$out,target=/out" --workdir /study --entrypoint python $image candidate.py --fixture /study/fixture.json --output /out/candidate.json *> (Join-Path $out 'candidate.container.log')
$candidateExit = $LASTEXITCODE
Set-Content -NoNewline (Join-Path $out 'candidate.exit.txt') $candidateExit
```

Proceed only if candidate exit is zero and exactly one nonempty `candidate.json` exists. Before the audit invocation, create a separate empty audit output directory and confirm no WSLc containers remain. The candidate output is mounted read-only to the auditor; audit output has its own writable bind mount.

```powershell
if ($candidateExit -ne 0) { throw 'STOP_CANDIDATE_NONZERO_NO_AUDIT' }
$auditOut = Join-Path $out 'audit-output'
if (Test-Path $auditOut) { throw 'STOP_AUDIT_OUTPUT_PATH_EXISTS' }
New-Item -ItemType Directory -Path $auditOut | Out-Null

wslc.exe run --rm --pull=never --network none --cpus 1 --memory 1g --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,source=$study,target=/study,readonly" --mount "type=bind,source=$out,target=/candidate,readonly" --mount "type=bind,source=$auditOut,target=/audit" --workdir /study --entrypoint python $image audit.py --fixture /study/fixture.json --candidate /candidate/candidate.json --output /audit/audit.json *> (Join-Path $out 'auditor.container.log')
$auditExit = $LASTEXITCODE
Set-Content -NoNewline (Join-Path $out 'auditor.exit.txt') $auditExit
```

The `--memory 1g` flag is recorded as configuration only. WSLc may warn that the kernel does not expose swap/cgroup limits; record the warning and do not claim enforcement unless the effective kernel limit is independently read back. This protocol omits `--gpus`; it makes no GPU, model, GUI, or input call. Source mounts are requested read-only. WSLc does not expose a read-only-root option in this workflow.

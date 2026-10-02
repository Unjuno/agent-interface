# WSLc commands — Issue 5663 T1

Pinned cached image: python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f; image ID 9e87977b8678. Recheck both at the formal start gate. This experiment is CPU-only; no GPU claim or lease is involved.

At the recorded bounded CPU/WSLc window, refetch main and stop if it differs from FREEZE.json. Verify source/input/freeze hashes, exact cached image, no running WSLc container or conflicting owner, and a fresh absent output directory. Do not pull/build. One candidate invocation; only on exit 0 and exactly one candidate.json, one separate raw-only auditor invocation; retries=0. Capture combined output and exit for both. Use --rm; inspect inventory before/after and do not remove prior stopped containers.

PowerShell from the repository root:

    $image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
    $study = (Resolve-Path '.\research\analysis\selection_variable_transport_5663_t1_20261002').Path
    $out = Join-Path (Get-Location) 'research\outputs\selection_variable_transport_5663_t1_20261002\formal-01'
    if (Test-Path $out) { throw 'STOP_OUTPUT_EXISTS' }
    New-Item -ItemType Directory -Path $out | Out-Null
    wslc.exe run --rm --pull=never --network none --cpus 1 --memory 512M --tmpfs /tmp:rw,nosuid,nodev,size=32m --mount "type=bind,source=$study,target=/study,readonly" --mount "type=bind,source=$out,target=/out" --workdir /study --entrypoint python $image -B candidate.py /study/inputs/fixture.json /out/candidate.json *> (Join-Path $out 'candidate.log')
    $candidateExit = [int]$LASTEXITCODE
    [System.IO.File]::WriteAllText((Join-Path $out 'candidate.exit.txt'), [string]$candidateExit)
    if ($candidateExit -ne 0) { throw 'STOP_CANDIDATE_EXIT' }
    $raw = Join-Path $out 'candidate.json'
    if (-not (Test-Path $raw) -or (Get-ChildItem $out -File -Filter 'candidate.json').Count -ne 1) { throw 'STOP_RAW_INVENTORY' }
    wslc.exe run --rm --pull=never --network none --cpus 1 --memory 512M --tmpfs /tmp:rw,nosuid,nodev,size=32m --mount "type=bind,source=$study,target=/study,readonly" --mount "type=bind,source=$raw,target=/raw/candidate.json,readonly" --workdir /study --entrypoint python $image -B audit.py /raw/candidate.json /study/inputs/fixture.json *> (Join-Path $out 'auditor.log')
    $auditorExit = [int]$LASTEXITCODE
    [System.IO.File]::WriteAllText((Join-Path $out 'auditor.exit.txt'), [string]$auditorExit)

Construction command, distinct from the one-shot allocation:

    python -B -m unittest -v research/analysis/selection_variable_transport_5663_t1_20261002/test_method.py

Host construction is not a formal result. Keep every construction attempt and failure separately. Do not infer effective memory enforcement from WSLc configuration; record warnings/cgroup/swap evidence if exposed.

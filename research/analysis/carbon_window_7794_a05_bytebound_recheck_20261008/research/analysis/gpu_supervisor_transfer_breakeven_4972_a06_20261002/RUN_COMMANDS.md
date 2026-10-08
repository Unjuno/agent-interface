# One-shot Docker invocation

PowerShell commands, run from the frozen local package directory after the start gate. The output directory must be new and empty, outside the read-only source mount.

PowerShell candidate command:

    $ErrorActionPreference = 'Stop'
    $image = 'pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067'
    $src = (Resolve-Path .).Path.Replace('\','/')
    $out = 'C:/Users/junny/Documents/Codex/2026-09-19/new-chat/gpu_a06_output_20261002'
    if (Test-Path $out) { throw 'STOP: output path exists' }
    New-Item -ItemType Directory -Path $out | Out-Null
    docker run --rm --pull=never --gpus all --network none --cpus=2 --memory=2g --pids-limit=128 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m -e AI_IMAGE_REF=$image -e AI_OUTPUT_DIR=/out -v "$($src):/study:ro" -v "$($out):/out:rw" --workdir /study --entrypoint python $image runner.py
    $candidateExit = $LASTEXITCODE

If and only if candidateExit is 0, and candidate_result.json exists exactly once, launch the separate raw-only CPU auditor once:

    docker run --rm --pull=never --network none --cpus=1 --memory=1g --pids-limit=64 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=32m -e AI_IMAGE_REF=$image -e AI_CANDIDATE_PATH=/out/candidate_result.json -e AI_OUTPUT_DIR=/out -v "$($src):/study:ro" -v "$($out):/out:rw" --workdir /study --entrypoint python $image audit.py

No retry, build, pull, or second candidate/auditor invocation. Retain complete stdout/stderr and exit codes.

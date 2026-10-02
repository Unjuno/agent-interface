# Allocation-07 commands

No command below authorizes a run. Use only after #5085 records an exact slot grant and every start gate passes.

## Candidate (Docker Desktop desktop-linux, RTX 3080)

```powershell
$image = 'pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067'
$src = (Resolve-Path .).Path.Replace('\','/')
$out = 'C:/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-gpu-a07-output'
if (Test-Path -LiteralPath $out) { throw 'STOP: output path exists' }
New-Item -ItemType Directory -Path $out | Out-Null
docker context use desktop-linux
docker run --rm --pull=never --gpus all --network none --cpus=2 --memory=2g --pids-limit=128 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m -e AI_IMAGE_REF=$image -e AI_OUTPUT_DIR=/out -v "${src}:/study:ro" -v "${out}:/out:rw" --workdir /study --entrypoint python $image runner.py
$candidateExit = $LASTEXITCODE
```

Only if the candidate exits 0 and exactly one candidate_result.json exists, invoke audit.py once in a separate CPU-only, network-disabled, read-only-root container against that result. Never rerun either invocation. Retain stdout/stderr, exact commands, GPU samples, and hashes.

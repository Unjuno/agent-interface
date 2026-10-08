# Frozen A04 one-shot run

Run in PowerShell from the checkout after committing the frozen package. Set `$repo` to this repository root and `$out` to a fresh sibling directory named `owner-keyup-duplicate-down-a04-results`.

```powershell
$repo = (Resolve-Path .).Path
$out = (Resolve-Path .\outputs\owner-keyup-duplicate-down-a04-results).Path
$image = 'python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016'
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src -e OUT_DIR=/out $image python -B /src/research/live_control/owner_keyup_duplicate_down_5156_a04_20261005/run_candidate.py *> "$out\candidate.log"
$candidateExit = $LASTEXITCODE
$candidateExit | Set-Content "$out\candidate.exit"
```

Only if the candidate exit is 0, invoke the auditor once in a new disposable container:

```powershell
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src $image python -B /src/research/live_control/owner_keyup_duplicate_down_5156_a04_20261005/audit.py /out/RESULT.json *> "$out\audit.log"
$auditExit = $LASTEXITCODE
$auditExit | Set-Content "$out\audit.exit"
```

Retain both logs/exits, raw result, audit JSON, and post-run hashes. Any image, source, mount, command, or execution mismatch is STOP. Do not retry either invocation. The pre-freeze fixture is development evidence and does not count as either formal invocation.

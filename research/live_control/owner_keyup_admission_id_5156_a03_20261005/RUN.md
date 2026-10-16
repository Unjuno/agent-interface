# Frozen A03 one-shot run

Run in PowerShell from the checkout, with `$repo` set to the repository root and `$out` to a fresh sibling directory named `owner-keyup-admission-id-a03-results`.

```powershell
$repo = (Resolve-Path .).Path
$out = (Resolve-Path .\outputs\owner-keyup-admission-id-a03-results).Path
$image = 'python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016'
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src -e OUT_DIR=/out $image python -B /src/research/live_control/owner_keyup_admission_id_5156_a03_20261005/run_candidate.py *> "$out\candidate.log"
$candidateExit = $LASTEXITCODE
$candidateExit | Set-Content "$out\candidate.exit"
```

Only if candidate exit is 0, invoke the auditor once in a new disposable container:

```powershell
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src $image python -B /src/research/live_control/owner_keyup_admission_id_5156_a03_20261005/audit.py /out/RESULT.json *> "$out\audit.log"
$auditExit = $LASTEXITCODE
$auditExit | Set-Content "$out\audit.exit"
```

Retain candidate/audit stdout and exits, raw result, audit JSON and post-run hashes. An image, source, inventory, mount, command, or execution mismatch is STOP; do not rerun either invocation.

# Frozen A02 one-shot execution

Run from PowerShell with `$repo` at this checkout and `$out` at a fresh sibling directory named `owner-keyup-context-join-a02-results`. Use the immutable image from `FREEZE.json`.

```powershell
$repo = (Resolve-Path .).Path
$out = (Resolve-Path .\outputs\owner-keyup-context-join-a02-results).Path
$image = 'python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016'
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src -e OUT_DIR=/out $image python -B /src/research/live_control/owner_keyup_context_join_5156_a02_20261005/run_candidate.py *> "$out\candidate.log"
$candidateExit = $LASTEXITCODE
$candidateExit | Set-Content "$out\candidate.exit"
```

Only if candidate exit is 0, invoke the auditor once:

```powershell
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src $image python -B /src/research/live_control/owner_keyup_context_join_5156_a02_20261005/audit.py /out/RESULT.json *> "$out\audit.log"
$auditExit = $LASTEXITCODE
$auditExit | Set-Content "$out\audit.exit"
```

Retain logs, exits, raw result, audit result, and hashes. Any frozen source, image, mount, inventory, or command mismatch is STOP. Do not rerun either invocation.

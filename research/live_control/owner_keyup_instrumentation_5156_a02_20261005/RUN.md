# Frozen A02 execution commands

Run from PowerShell with `$repo` set to this worktree and `$out` to a fresh separate writable directory named `5156-owner-keyup-instrumentation-a02-20261005-results`. Use the immutable image digest from `FREEZE.json`. Candidate and auditor run once in separate disposable containers, with no network, one CPU, and a read-only source mount. Do not set a memory limit on this host.

```powershell
$repo = (Resolve-Path .).Path
$out = (Resolve-Path .\outputs\5156-owner-keyup-instrumentation-a02-20261005-results).Path
$image = 'python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016'
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src -e OUT_DIR=/out $image python -B /src/research/live_control/owner_keyup_instrumentation_5156_a02_20261005/run_candidate.py *> "$out\candidate.log"
$candidateExit = $LASTEXITCODE
$candidateExit | Set-Content "$out\candidate.exit"
```

Only if candidate exit is 0:

```powershell
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src $image python -B /src/research/live_control/owner_keyup_instrumentation_5156_a02_20261005/audit.py /out/RESULT.json *> "$out\audit.log"
$auditExit = $LASTEXITCODE
$auditExit | Set-Content "$out\audit.exit"
```

Retain logs, exits, `RESULT.json`, `AUDIT.json`, and hashes. Stop on any image, source, inventory, mount, or command mismatch. Never rerun either frozen invocation.

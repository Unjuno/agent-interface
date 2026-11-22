# Frozen execution commands

Run from PowerShell with the repository root at `$repo` and the separate output directory at `$out`. The inspected local image is referenced by immutable RepoDigest. Candidate and auditor use distinct disposable containers, no network, one CPU, a read-only source bind, and a separate writable output bind. Memory limiting is omitted because this host has no demonstrated cgroup memory enforcement.

```powershell
$repo = (Resolve-Path .).Path
$out = (Resolve-Path .\outputs\5156-owner-keyup-instrumentation-a01-20261005-results).Path
$image = 'python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016'
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src -e OUT_DIR=/out $image python -B /src/research/live_control/owner_keyup_instrumentation_5156_a01_20261005/run_candidate.py *> "$out\candidate.log"
$candidateExit = $LASTEXITCODE
$candidateExit | Set-Content "$out\candidate.exit"
```

Only if that candidate exits 0, invoke the independent auditor exactly once:

```powershell
wslc run --rm --pull never --network none --cpus 1 --volume "${repo}:/src:ro" --volume "${out}:/out:rw" --workdir /src $image python -B /src/research/live_control/owner_keyup_instrumentation_5156_a01_20261005/audit.py /out/RESULT.json *> "$out\audit.log"
$auditExit = $LASTEXITCODE
$auditExit | Set-Content "$out\audit.exit"
```

Do not rerun either invocation or substitute an image/source after the run. Preserve both exit files, logs, `RESULT.json`, and `AUDIT.json` with their hashes. Any identity, mount, inventory, or command mismatch is STOP.

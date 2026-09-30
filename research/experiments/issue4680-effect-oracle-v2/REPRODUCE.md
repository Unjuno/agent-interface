# Reproduction of the retained failed v2 first outcome

The first outcome for this allocation is final and must not be retried or tuned. This command is provided to reproduce the historical failure from a fresh checkout, not to replace it. Run from the repository root, using a fresh output directory outside the read-only source mount:

```powershell
$experiments=(Resolve-Path 'research\experiments').Path
$out=Join-Path $env:TEMP 'issue4680-effect-oracle-v2-reproduction-output'
if (Test-Path -LiteralPath $out) { throw "Choose a fresh output directory: $out" }
New-Item -ItemType Directory -Path $out | Out-Null
docker run --rm --network none --cpus 1 --memory 128m --pids-limit 16 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --security-opt no-new-privileges --cap-drop ALL --mount "type=bind,source=$experiments,target=/work,readonly" --mount "type=bind,source=$out,target=/out" --entrypoint python python:3.11-slim -B /work/issue4680-effect-oracle-v2/execute.py /out /work/issue4680-skillpackage-construction
```

Expected historical outcome: exit 1 at the one `already_satisfied` oracle test. The formal audit and corruption controls do not run. Never alter or overwrite committed raw outputs; any new semantics require a distinct allocation.


# Reproduction (Windows PowerShell + Docker Desktop)

Use a fresh empty output directory per execution. Do not mount an existing output directory from an earlier attempt.

```powershell
$src = (Resolve-Path 'C:\path\to\issue4680-skillpackage-construction').Path
$out = 'C:\path\to\fresh-empty-output'
New-Item -ItemType Directory -Path $out | Out-Null
docker run --rm --network none --cpus 1 --memory 256m --pids-limit 32 --read-only `
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --security-opt no-new-privileges --cap-drop ALL `
  --mount "type=bind,source=$src,target=/src,readonly" `
  --mount "type=bind,source=$out,target=/out" `
  --entrypoint python python:3.11-slim -B /src/execute.py /out
```

The construction runner verifies every source hash in `FREEZE.json`, executes the 8-test suite and exactly one 10-row proposal run, then audits the raw result and copies four mutations for rejection. The original controls wrapper has a retained decision-label comparison bug; `controls_audit_v2.py` is a separate read-only reclassification of those already-retained mutation outputs and does not rerun the runner or auditor.

This reproduction remains a construction-only HOLD: proposals and snapshot discipline are exercised, but no action is applied to an independent effect simulator and no adapted Needle/backend comparison is performed.


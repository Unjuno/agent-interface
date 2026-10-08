# Formal WSLc invocation plan — Issue #6615 T0

Status: not launched. These are frozen command forms, not an allocation or permission.

Pinned image reference: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Confirm exact cached digest and platform on the assigned WSLc host before the run; never pull.

Use the package directory as read-only `/study`. Create two fresh, distinct output directories only after exact WSLc host/CPU-lane assignment, inventory and source-hash checks. Candidate and auditor are separate single invocations. On candidate nonzero exit, preserve it and do not run audit. Retries are zero.

```powershell
$image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$study = '<absolute-package-path>'
$candidateOut = '<fresh-candidate-output-path>'
$auditOut = '<fresh-auditor-output-path>'

wslc.exe run --rm --pull=never --network none --cpus 0.25 --memory 256m `
  --mount "type=bind,source=$study,target=/study,readonly" `
  --mount "type=bind,source=$candidateOut,target=/out" `
  --workdir /study --entrypoint python $image -B candidate.py /study/fixture.json /out/candidate.json

# Only if the candidate exits 0 and exactly one candidate.json exists:
wslc.exe run --rm --pull=never --network none --cpus 0.25 --memory 256m `
  --mount "type=bind,source=$study,target=/study,readonly" `
  --mount "type=bind,source=$candidateOut,target=/candidate,readonly" `
  --mount "type=bind,source=$auditOut,target=/out" `
  --workdir /study --entrypoint python $image -B auditor.py /study/fixture.json /candidate/candidate.json /out/audit.json
```

Capture exact stdout/stderr, exit codes, WSLc version, host identity, cached image ID/platform, pre/post container inventory, elapsed wall times, and any cgroup/swap warning. Do not infer enforcement from requested limits. Keep output logs and hashes immutable; no Docker/OrbStack fallback.

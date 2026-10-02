# Formal WSLc command forms — Issue #6645 T0

Not launched. The following forms are frozen as the one-shot plan; they are not
an allocation or permission. Verify assigned host, WSLc version, cached image
digest/platform, clean pre/post inventory, fresh output directories, current
main ancestry, and every FREEZE hash before invoking. No pull, network, GPU,
GUI, task input, or retry.

```powershell
$image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$study = '<absolute-package-path>'
$candidateOut = '<fresh-candidate-output-directory>'
$auditOut = '<fresh-auditor-output-directory>'

wslc.exe run --rm --pull=never --network none --cpus 0.25 --memory 256m `
  --tmpfs /tmp:rw,nosuid,nodev,size=32m `
  --mount "type=bind,source=$study,target=/study,readonly" `
  --mount "type=bind,source=$candidateOut,target=/out" `
  --workdir /study --entrypoint python $image -B candidate.py /study/fixture.json /out/candidate_raw.json

# Only if candidate exits 0 and exactly one raw output exists:
wslc.exe run --rm --pull=never --network none --cpus 0.25 --memory 256m `
  --tmpfs /tmp:rw,nosuid,nodev,size=32m `
  --mount "type=bind,source=$study,target=/study,readonly" `
  --mount "type=bind,source=$candidateOut,target=/candidate,readonly" `
  --mount "type=bind,source=$auditOut,target=/audit" `
  --workdir /study --entrypoint python $image -B auditor.py /study/fixture.json /candidate/candidate_raw.json /audit/audit.json
```

Record stdout/stderr, exit codes, elapsed host time, WSLc/container versions,
image ID/platform, inventory before/after, and cgroup/swap warnings. Requested
resource limits are not proof of enforcement. The auditor gets fixture and raw
only; it does not import candidate code. No Docker/OrbStack fallback.

# One-shot audit-only WSLc command

Run only after the freeze is posted to Issue #6410, code/input hashes pass, output is empty, WSLc has no active sibling container, and the shared-runtime owner check is clear. Do not pull or build an image. This is the only formal container invocation: candidate=0, auditor=1, retries=0.

From PowerShell:

```powershell
$IMAGE = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$AUDIT = (Resolve-Path .\research\analysis\needle_role_skill_lifecycle_6410_audit_20261002).Path
$EVIDENCE = (Resolve-Path ..\needle-role-skill-lifecycle-wslc-5084-20261002\research).Path
$OUT = (Resolve-Path .\audit-output).Path
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 `
  --mount "type=bind,source=$AUDIT,target=/src,readonly" `
  --mount "type=bind,source=$EVIDENCE,target=/evidence,readonly" `
  --mount "type=bind,source=$OUT,target=/out" `
  -w /src --entrypoint python $IMAGE -B audit.py `
  --freeze /src/FREEZE.json `
  --raw /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/formal-output/raw.json `
  --skill /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json `
  --expected /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/expected.json `
  --original-freeze /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/FREEZE.json `
  --scorer /evidence/analysis/needle_role_skill_lifecycle_4916_first_rung_v2/lifecycle_corrected.py `
  --legacy-sources /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002 `
  --validator /evidence/analysis/needle_role_skill_lifecycle_4916_v2/lifecycle.py `
  --out /out/audit.json
```

Retain the exact exit code, complete stdout/stderr including any WSLc resource warning, `audit.json`, and post-run SHA-256 values. Do not retry if the process starts and fails; classify and preserve that outcome. `--memory 512m` is requested, not proof that a cgroup limit was enforced.

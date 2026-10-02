# Allocation 03 — one-shot raw-only WSLc audit

Do not run this script until the exact bounded CPU/WSLc allocation is explicitly assigned and the current runtime owner has confirmed release. A local idle inventory is not a grant. Candidate=0; auditor=1 maximum; retries=0.

Run from a clean checkout of branch `research/needle-role-skill-lifecycle-6410-audit-a03-20261002`:

```powershell
$RepoRoot = (git rev-parse --show-toplevel).Trim()
$ExpectedMain = '49144844b482026c33fcfbde7e2fd5f7bdc7762c'
git fetch origin main
$LiveMain = (git rev-parse origin/main).Trim()
if ($LiveMain -ne $ExpectedMain) { throw "STOP: main advanced; refreeze before any formal invocation" }

$Package = Join-Path $RepoRoot 'research\\analysis\\needle_role_skill_lifecycle_6410_audit_a03_20261002'
$Evidence = Join-Path $RepoRoot 'research'
$Freeze = Get-Content -Raw (Join-Path $Package 'FREEZE.json') | ConvertFrom-Json
if ($Freeze.allocation -ne 'NEEDLE-ROLE-SKILL-LIFECYCLE-WSLC-6410-AUDIT-20261002-03') { throw 'STOP: wrong allocation' }
$Out = Join-Path $Package 'results\audit-03'
if (Test-Path -LiteralPath $Out) { throw 'STOP: output path already exists' }

$Expected = @{
  'analysis\needle_role_skill_lifecycle_wslc_5084_t0_20261002\formal-output\raw.json' = 'bef4b5fbd98f5743ca597406b83414bb695657aa611d2898063dc370f793cbcf'
  'analysis\needle_role_skill_lifecycle_wslc_5084_t0_20261002\FREEZE.json' = 'e0338a6c72afe8797e911653069d318373269cd5b642d2fab3cbce9cd9529ef9'
  'needle_role_skill_reload_3780_v1\formal\seed-3788\builder\skill.json' = '2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a'
  'needle_role_skill_reload_3780_v1\formal\seed-3788\builder\expected.json' = '5baca462abbcdd561dba4c790775a589f91a0fa15453e2f3e6c3bc74fb1b6f61'
  'analysis\needle_role_skill_lifecycle_4916_first_rung_v2\lifecycle_corrected.py' = 'd8a7292430968f388159bb3dd1fb3f4523381d95691b07d99087f49553d4f8e3'
  'analysis\needle_role_skill_lifecycle_4916_v2\lifecycle.py' = 'e45a6b1ec6ad4995533c59d3ae560b9a91e2d31b2d7186c1cae5705f90602b80'
}
foreach ($relative in $Expected.Keys) {
  $path = Join-Path $Evidence $relative
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "STOP: missing host input $relative" }
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
  if ($actual -ne $Expected[$relative]) { throw "STOP: hash mismatch $relative" }
}
$Image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$AuditDir = $Package
$EvidenceRoot = $Evidence
$null = New-Item -ItemType Directory -Path $Out
$ContainerScript = 'for p in /src/FREEZE.json /src/audit.py /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/formal-output/raw.json /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/FREEZE.json /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/expected.json /evidence/analysis/needle_role_skill_lifecycle_4916_first_rung_v2/lifecycle_corrected.py /evidence/analysis/needle_role_skill_lifecycle_4916_v2/lifecycle.py; do test -f "$p"; done; exec python -B audit.py --freeze /src/FREEZE.json --raw /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/formal-output/raw.json --skill /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json --expected /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/expected.json --original-freeze /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/FREEZE.json --scorer /evidence/analysis/needle_role_skill_lifecycle_4916_first_rung_v2/lifecycle_corrected.py --legacy-sources /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002 --validator /evidence/analysis/needle_role_skill_lifecycle_4916_v2/lifecycle.py --out /out/audit.json'
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 `
  --mount "type=bind,source=$AuditDir,target=/src,readonly" `
  --mount "type=bind,source=$EvidenceRoot,target=/evidence,readonly" `
  --mount "type=bind,source=$Out,target=/out" `
  -w /src --entrypoint /bin/sh $Image -ec $ContainerScript
$ExitCode = $LASTEXITCODE
# Preserve stdout/stderr, exact exit code, audit.json if emitted, and cgroup/swap warnings.
# Never retry this invocation. Hash the output bundle and append the terminal result.
```

Container-side preflight uses the exact same paths as the auditor arguments. The host preflight independently verifies the frozen input digests before starting WSLc. If either gate fails, no replacement invocation is permitted under this allocation.

# Allocation 03 — one-shot raw-only WSLc audit

This command is a prepared protocol, **not authorization**. Do not run it until an exact bounded CPU/WSLc assignment to this allocation and the current shared-runtime owner's explicit release are recorded in #5085. Local idle-container/GPU snapshots do not grant a lane. Candidate=0; auditor=1 maximum; retries=0.

Run from a clean checkout of branch `research/needle-role-skill-lifecycle-6410-audit-a03-20261002`. The freeze is prospective; refreeze only before invocation if main has advanced, update its manifest hash, and re-check source/input identities and the exact allocation. Do not invoke if a gate is ambiguous.

```powershell
$RepoRoot = (git rev-parse --show-toplevel).Trim()
git fetch origin main
$Package = Join-Path $RepoRoot 'research\analysis\needle_role_skill_lifecycle_6410_audit_a03_20261002'
$Evidence = Join-Path $RepoRoot 'research'
$FreezePath = Join-Path $Package 'FREEZE.json'
$Freeze = Get-Content -Raw $FreezePath | ConvertFrom-Json
$ExpectedAllocation = 'NEEDLE-ROLE-SKILL-LIFECYCLE-WSLC-6410-AUDIT-20261002-03'
if ($Freeze.allocation -ne $ExpectedAllocation) { throw 'STOP: wrong allocation' }

# Fill these only from the exact owner/coordinator assignment recorded in #5085.
$AssignedAllocation = 'UNASSIGNED'
$OwnerReleaseConfirmed = $false
if ($AssignedAllocation -ne $ExpectedAllocation -or -not $OwnerReleaseConfirmed) { throw 'STOP: no exact allocation grant and owner release' }

$LiveMain = (git rev-parse origin/main).Trim()
if ($LiveMain -ne $Freeze.base_commit) { throw 'STOP: main advanced; refreeze and re-review before any formal invocation' }

$Out = Join-Path $Package 'results\audit-03'
if (Test-Path -LiteralPath $Out) { throw 'STOP: output path already exists' }

$Expected = @{
  'analysis\needle_role_skill_lifecycle_wslc_5084_t0_20261002\formal-output\raw.json' = 'bef4b5fbd98f5743ca597406b83414bb695657aa611d2898063dc370f793cbcf'
  'analysis\needle_role_skill_lifecycle_wslc_5084_t0_20261002\FREEZE.json' = 'e0338a6c72afe8797e911653069d318373269cd5b642d2fab3cbce9cd9529ef9'
  'analysis\needle_role_skill_lifecycle_wslc_5084_t0_20261002\candidate.py' = '3d5b18a2ff3b493f78440ac10c77ae2583f1ea05048fc37b35d76674f88e037f'
  'analysis\needle_role_skill_lifecycle_wslc_5084_t0_20261002\audit.py' = '30e12c5de4f28926fc9cdc6c77cbcd25381daebf11078ea58894b39cca7ecc09'
  'analysis\needle_role_skill_lifecycle_wslc_5084_t0_20261002\test_contract.py' = 'b955786caef447266f3b2bd55a71d3afecf7a1b4829fadfe9c0bbf36a11375a9'
  'needle_role_skill_reload_3780_v1\formal\seed-3788\builder\skill.json' = '2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a'
  'needle_role_skill_reload_3780_v1\formal\seed-3788\builder\expected.json' = '5baca462abbcdd561dba4c790775a589f91a0fa15453e2f3e6c3bc74fb1b6f61'
  'analysis\needle_role_skill_lifecycle_4916_first_rung_v2\lifecycle_corrected.py' = 'd8a7292430968f388159bb3dd1fb3f4523381d95691b07d99087f49553d4f8e3'
  'analysis\needle_role_skill_lifecycle_4916_v2\lifecycle.py' = 'e45a6b1ec6ad4995533c59d3ae560b9a91e2d31b2d7186c1cae5705f90602b80'
}
foreach ($relative in $Expected.Keys) {
  $inputPath = Join-Path $Evidence $relative
  if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) { throw "STOP: missing host input $relative" }
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $inputPath).Hash.ToLowerInvariant()
  if ($actual -ne $Expected[$relative]) { throw "STOP: hash mismatch $relative" }
}

$Image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$null = New-Item -ItemType Directory -Path $Out
$ContainerScript = 'for p in /src/FREEZE.json /src/audit.py /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/formal-output/raw.json /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/FREEZE.json /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/candidate.py /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/audit.py /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/test_contract.py /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/expected.json /evidence/analysis/needle_role_skill_lifecycle_4916_first_rung_v2/lifecycle_corrected.py /evidence/analysis/needle_role_skill_lifecycle_4916_v2/lifecycle.py; do test -f "$p"; done; exec python -B audit.py --freeze /src/FREEZE.json --raw /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/formal-output/raw.json --skill /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json --expected /evidence/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/expected.json --original-freeze /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/FREEZE.json --scorer /evidence/analysis/needle_role_skill_lifecycle_4916_first_rung_v2/lifecycle_corrected.py --legacy-sources /evidence/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002 --validator /evidence/analysis/needle_role_skill_lifecycle_4916_v2/lifecycle.py --out /out/audit.json'
$Console = & wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 `
  --mount "type=bind,source=$Package,target=/src,readonly" `
  --mount "type=bind,source=$Evidence,target=/evidence,readonly" `
  --mount "type=bind,source=$Out,target=/out" `
  -w /src --entrypoint /bin/sh $Image -ec $ContainerScript 2>&1
$ExitCode = $LASTEXITCODE
$Console | Out-File -LiteralPath (Join-Path $Out 'auditor.console.log') -Encoding utf8
"WSLC_EXIT_CODE=$ExitCode" | Out-File -LiteralPath (Join-Path $Out 'auditor.exit.txt') -Encoding ascii
# Preserve raw audit.json if emitted. Record all post-run hashes and the exact terminal outcome.
# Do not repeat this invocation, including when the in-container path preflight fails.
```

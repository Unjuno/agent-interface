$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$freezePath = Join-Path $root 'FREEZE.json'
$fixturePath = Join-Path $root 'fixture.json'
$outDir = Join-Path $root 'formal-output-01'
$freeze = Get-Content -Raw -LiteralPath $freezePath | ConvertFrom-Json
if (-not $freeze.allocation_id -or -not $freeze.main_sha) { throw 'freeze identity missing' }
if (Test-Path -LiteralPath $outDir) { throw "output collision: $outDir" }
foreach ($entry in $freeze.source_sha256.PSObject.Properties) {
  $path = Join-Path $root $entry.Name
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
  if ($actual -ne $entry.Value) { throw "source hash mismatch: $($entry.Name)" }
}
New-Item -ItemType Directory -Path $outDir | Out-Null
$candidatePath = Join-Path $outDir 'candidate.json'
$candidateStdout = Join-Path $outDir 'candidate.stdout.txt'
$candidateStderr = Join-Path $outDir 'candidate.stderr.txt'
$auditPath = Join-Path $outDir 'audit.json'
$auditStdout = Join-Path $outDir 'auditor.stdout.txt'
$auditStderr = Join-Path $outDir 'auditor.stderr.txt'
$started = [DateTime]::UtcNow.ToString('o')
& python (Join-Path $root 'candidate.py') --fixture $fixturePath --freeze $freezePath --output $candidatePath 1> $candidateStdout 2> $candidateStderr
$candidateExit = $LASTEXITCODE
$auditExit = $null
if ($candidateExit -eq 0) {
  & python (Join-Path $root 'auditor.py') --fixture $fixturePath --freeze $freezePath --candidate $candidatePath --output $auditPath 1> $auditStdout 2> $auditStderr
  $auditExit = $LASTEXITCODE
}
$finished = [DateTime]::UtcNow.ToString('o')
$record = [ordered]@{
  schema = 'agent-interface/6222-crossed-verdict-run-v1'
  allocation_id = $freeze.allocation_id
  main_sha = $freeze.main_sha
  started_utc = $started
  finished_utc = $finished
  candidate_invocations = 1
  candidate_exit_code = $candidateExit
  auditor_invocations = $(if ($candidateExit -eq 0) { 1 } else { 0 })
  auditor_exit_code = $auditExit
  host = $env:COMPUTERNAME
  python = (python --version 2>&1 | Out-String).Trim()
  candidate_sha256 = if (Test-Path $candidatePath) { (Get-FileHash -Algorithm SHA256 $candidatePath).Hash.ToLowerInvariant() } else { $null }
  audit_sha256 = if (Test-Path $auditPath) { (Get-FileHash -Algorithm SHA256 $auditPath).Hash.ToLowerInvariant() } else { $null }
  disposition = if ($candidateExit -ne 0) { 'STOP_CANDIDATE_NONZERO' } elseif ($auditExit -ne 0) { 'FAIL_AUDIT_NONZERO' } else { 'AUDIT_EXIT_ZERO_REQUIRES_CONTENT_REVIEW' }
}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $outDir 'RUN.json') -Encoding utf8
$files = Get-ChildItem -LiteralPath $outDir -File | Where-Object Name -ne 'SHA256SUMS' | Sort-Object Name
$lines = foreach ($file in $files) { "{0}  {1}" -f (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToLowerInvariant(), $file.Name }
$lines | Set-Content -LiteralPath (Join-Path $outDir 'SHA256SUMS') -Encoding utf8
Get-Content -Raw -LiteralPath (Join-Path $outDir 'RUN.json')
if ($candidateExit -ne 0) { exit $candidateExit }
if ($auditExit -ne 0) { exit $auditExit }


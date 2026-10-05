$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $here 'results/formal-01'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$python = (Get-Command python -ErrorAction Stop).Source
$started = [DateTime]::UtcNow.ToString('o')
$candidateOut = Join-Path $out 'candidate.stdout.txt'
$candidateErr = Join-Path $out 'candidate.stderr.txt'
$auditOut = Join-Path $out 'auditor.stdout.txt'
$auditErr = Join-Path $out 'auditor.stderr.txt'
$candidateExit = $null
$auditExit = $null

try {
    $candidateResult = Start-Process -FilePath $python -ArgumentList @('-B', (Join-Path $here 'candidate.py')) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $candidateOut -RedirectStandardError $candidateErr
    $candidateExit = $candidateResult.ExitCode
    if ($candidateExit -eq 0) {
        $auditResult = Start-Process -FilePath $python -ArgumentList @('-B', (Join-Path $here 'audit.py')) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $auditOut -RedirectStandardError $auditErr
        $auditExit = $auditResult.ExitCode
    }
} finally {
    $ended = [DateTime]::UtcNow.ToString('o')
    $run = [ordered]@{
        schema = 'preference-manipulation-7678-t0-run-v1'
        allocation = 'PREFERENCE-MANIPULATION-7678-T0-20261005-01'
        started_utc = $started
        ended_utc = $ended
        host = [Environment]::OSVersion.VersionString
        python = (& $python --version 2>&1 | Out-String).Trim()
        candidate_exit_code = $candidateExit
        auditor_exit_code = $auditExit
        retry_count = 0
        status = if ($candidateExit -ne 0) { 'FAIL_CANDIDATE' } elseif ($auditExit -ne 0) { 'FAIL_AUDIT' } else { 'AUDIT_COMPLETED_CHECK_REPORT' }
    }
    $run | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'RUN.json') -Encoding utf8
}

if ($candidateExit -ne 0) { exit $candidateExit }
if ($auditExit -ne 0) { exit $auditExit }
exit 0

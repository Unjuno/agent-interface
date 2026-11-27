param(
    [ValidateRange(1, 3600)][int]$CliTimeoutSeconds = 10,
    [ValidateRange(1, 3600)][int]$RunTimeoutSeconds = 90,
    [ValidateRange(1, 3600)][int]$CleanupTimeoutSeconds = 15
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'wslc_bounded_process.psm1') -Force

function Invoke-ProbeCli {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][ValidateRange(1, 3600)][int]$TimeoutSeconds,
        [Parameter(Mandatory)][string]$LogName,
        [System.Text.Encoding]$OutputEncoding
    )

    $result = Invoke-WslcBoundedProcess -FilePath $FilePath `
        -ArgumentList $Arguments -TimeoutSeconds $TimeoutSeconds `
        -OutputEncoding $OutputEncoding
    [System.IO.File]::WriteAllText((Join-Path $probePath "$LogName.stdout.txt"),
        $result.StandardOutput, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText((Join-Path $probePath "$LogName.stderr.txt"),
        $result.StandardError, [System.Text.UTF8Encoding]::new($false))
    if (-not [string]::IsNullOrEmpty($result.StandardOutput)) {
        [Console]::Out.Write($result.StandardOutput)
    }
    if (-not [string]::IsNullOrEmpty($result.StandardError)) {
        [Console]::Error.Write($result.StandardError)
    }
    if ($result.TimedOut) {
        throw "CLI timed out after ${TimeoutSeconds}s (pid=$($result.ProcessId)); runtime outcome is UNKNOWN."
    }
    if ($result.ExitCode -ne 0) {
        throw "CLI exited $($result.ExitCode); runtime outcome may be UNKNOWN."
    }
    return $result
}

function Confirm-ProbeContainerAbsent {
    param([Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{64}$')][string]$ContainerId)

    # Query only this run's exact container ID; never enumerate unrelated shared containers.
    $cleanupQuery = Invoke-ProbeCli -FilePath $wslc.Source `
        -Arguments @('container', 'list', '--all', '--filter', "id=$ContainerId", '--format', 'json') `
        -TimeoutSeconds $CleanupTimeoutSeconds -LogName 'wslc-cleanup-query'
    $listing = ($cleanupQuery.StandardOutput -split "`r?`n" -join "`n").Trim()
    # WSLc 3.0.1 emits no stdout for a successful zero-match filtered query.
    # PowerShell also unwraps ConvertFrom-Json's empty array to $null, so
    # recognize only the exact empty JSON array before parsing other responses.
    if ($listing -match '^\[\s*\]$') {
        $listing = ''
    }
    if (-not [string]::IsNullOrWhiteSpace($listing)) {
        try {
            $listedContainers = ConvertFrom-Json -InputObject $listing -ErrorAction Stop
        }
        catch {
            throw 'The scoped WSLc cleanup query returned invalid JSON; cleanup is unverified.'
        }
        if ($null -eq $listedContainers -or @($listedContainers).Count -gt 0) {
            throw 'The scoped WSLc cleanup query returned a matching container; cleanup is unverified.'
        }
    }
}

$wslc = Get-Command wslc.exe -ErrorAction SilentlyContinue
if (-not $wslc) {
    throw 'wslc.exe is required. Update WSL to 2.9.3 or later, then reopen PowerShell.'
}
$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $wsl) {
    throw 'wsl.exe is required to record the WSL runtime version.'
}

$image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$evidenceRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$probePath = [System.IO.Path]::GetFullPath((Join-Path $evidenceRoot 'run'))
if (-not $probePath.StartsWith($evidenceRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing to create a probe directory outside this evidence packet.'
}
if (Test-Path -LiteralPath $probePath) { throw 'Refusing to overwrite the one-shot WSLc evidence directory.' }

$containerName = "agent-interface-wslc-s01-$([guid]::NewGuid().ToString('N'))"
$cidPath = Join-Path $probePath 'container.cid'
$sentinelPath = Join-Path $probePath 'sentinel.bin'
$preserveProbePath = $false
$probeCode = @'
import errno
from pathlib import Path

sentinel = Path("/probe/sentinel.bin")
if sentinel.read_bytes() != b"wslc-readonly-probe":
    raise SystemExit("mounted source bytes differ")
try:
    sentinel.write_bytes(b"must-not-write")
except OSError as error:
    if error.errno != errno.EROFS:
        raise
    print("read-only bind mount: PASS (EROFS)")
else:
    raise SystemExit("read-only bind mount unexpectedly allowed a write")
'@

try {
    $null = New-Item -ItemType Directory -Path $probePath
    [System.IO.File]::WriteAllText((Join-Path $probePath 'container-name.txt'), $containerName, [System.Text.UTF8Encoding]::new($false))
    Write-Output 'WSL version:'
    Invoke-ProbeCli -FilePath $wsl.Source -Arguments @('--version') `
        -TimeoutSeconds $CliTimeoutSeconds -LogName 'wsl-version' `
        -OutputEncoding ([System.Text.Encoding]::Unicode) | Out-Null
    Write-Output 'WSLc version:'
    Invoke-ProbeCli -FilePath $wslc.Source -Arguments @('version') `
        -TimeoutSeconds $CliTimeoutSeconds -LogName 'wslc-version' | Out-Null

    [System.IO.File]::WriteAllBytes($sentinelPath, [System.Text.Encoding]::UTF8.GetBytes('wslc-readonly-probe'))

    # Once run starts, retain the unique probe directory until exact-container
    # cleanup has been confirmed. A timed-out CLI exit does not cancel server work.
    $preserveProbePath = $true
    $runFailure = $null
    try {
        Invoke-ProbeCli -FilePath $wslc.Source -Arguments @('run', '--rm', '--name',
            $containerName, '--cidfile', $cidPath, '--pull', 'never', '--network',
            'none', '--memory', '512M', '--cpus', '1', '--volume',
            "${probePath}:/probe:ro", $image, 'python', '-B', '-c', $probeCode) `
            -TimeoutSeconds $RunTimeoutSeconds -LogName 'wslc-run' | Out-Null
    }
    catch {
        $runFailure = $_.Exception.Message
    }

    if (-not (Test-Path -LiteralPath $cidPath -PathType Leaf)) {
        if ($runFailure) {
            throw "WSLc run failed: $runFailure; no full container ID receipt exists, so cleanup is unverified."
        }
        throw 'WSLc probe completed without writing its requested container ID receipt.'
    }

    $containerId = (Get-Content -LiteralPath $cidPath -Raw).Trim()
    if ($containerId -notmatch '^[0-9a-fA-F]{64}$') {
        if ($runFailure) {
            throw "WSLc run failed: $runFailure; the container ID receipt is malformed, so cleanup is unverified."
        }
        throw 'WSLc probe wrote a missing or malformed full container ID receipt.'
    }

    if ($runFailure) {
        try {
            Confirm-ProbeContainerAbsent -ContainerId $containerId
        }
        catch {
            throw "WSLc run failed: $runFailure; exact-CID cleanup query was inconclusive: $($_.Exception.Message)"
        }
        throw "WSLc run failed: $runFailure; exact-CID cleanup query found no matching container. Runtime-side timeout completion and application outcome remain unverified."
    }

    Confirm-ProbeContainerAbsent -ContainerId $containerId

    Write-Output 'WSLc local runtime probe: PASS'
    Write-Output "Image: $image"
    Write-Output 'Network: none; memory: 512M; CPUs: 1; source mount: read-only; cleanup: verified'
    Write-Output 'Note: WSL may report that swap/cgroup memory limits are unavailable; this probe does not test swap isolation or peak-memory enforcement.'
    $preserveProbePath = $false
}
finally {
    if (Test-Path -LiteralPath $probePath) {
        if ($preserveProbePath) {
            Write-Warning "Probe/runtime outcome is unconfirmed. Preserved receipts and logs at $probePath; do not retry before reconciling this unique probe."
        }
        else {
            Write-Output "Completed-run receipts retained at $probePath"
        }
    }
}

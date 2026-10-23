$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'wslc_bounded_process.psm1') -Force
$powershell = (Get-Command powershell.exe -ErrorAction Stop).Source

$normal = Invoke-WslcBoundedProcess -FilePath $powershell -TimeoutSeconds 10 `
    -ArgumentList @('-NoProfile', '-NonInteractive', '-Command',
        '[Console]::Out.WriteLine("stdout with spaces"); [Console]::Error.WriteLine("stderr marker"); exit 7')
if ($normal.TimedOut -or $normal.ExitCode -ne 7) {
    throw "Normal child result mismatch: $($normal | ConvertTo-Json -Compress)"
}
if ($normal.StandardOutput -notmatch 'stdout with spaces' -or
        $normal.StandardError -notmatch 'stderr marker') {
    throw "Child argument or output capture mismatch: $($normal | ConvertTo-Json -Compress)"
}

$timer = [System.Diagnostics.Stopwatch]::StartNew()
$timeout = Invoke-WslcBoundedProcess -FilePath $powershell -TimeoutSeconds 1 `
    -ArgumentList @('-NoProfile', '-NonInteractive', '-Command', 'Start-Sleep -Seconds 30')
$timer.Stop()
if (-not $timeout.TimedOut -or $null -ne $timeout.ExitCode) {
    throw "Expected explicit timeout result: $($timeout | ConvertTo-Json -Compress)"
}
if ($timer.Elapsed.TotalSeconds -ge 5) {
    throw "Timeout exceeded the 1s bound by too much: $($timer.Elapsed.TotalSeconds)s"
}
if (Get-Process -Id $timeout.ProcessId -ErrorAction SilentlyContinue) {
    throw "Timed-out CLI child $($timeout.ProcessId) remained alive."
}

$unicode = Invoke-WslcBoundedProcess -FilePath $powershell -TimeoutSeconds 10 `
    -ArgumentList @('-NoProfile', '-NonInteractive', '-Command',
        '[Console]::OutputEncoding = [System.Text.Encoding]::Unicode; [Console]::Error.WriteLine("stderr unicode marker"); [Console]::Out.WriteLine("stdout unicode marker"); exit 0') `
    -OutputEncoding ([System.Text.Encoding]::Unicode)
if ($unicode.TimedOut -or $unicode.ExitCode -ne 0 -or
        $unicode.StandardOutput -notmatch 'stdout unicode marker' -or
        $unicode.StandardError -notmatch 'stderr unicode marker' -or
        $unicode.StandardOutput.Contains([char]0) -or
        $unicode.StandardError.Contains([char]0)) {
    throw "Unicode child output decoding mismatch: $($unicode | ConvertTo-Json -Compress)"
}

Write-Output 'Bounded child output/exit/timeout checks: PASS (3 cases)'

param([string]$OutputPath)
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'wslc_cleanup_receipt.psm1') -Force

$containerId = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
$cases = @(
    @{ case_id = 'empty-array'; exit_code = 0; raw_response = '[]'; want_absence = $true },
    @{ case_id = 'empty-array-whitespace'; exit_code = 0; raw_response = " [ `n ] "; want_absence = $true },
    @{ case_id = 'remaining-row'; exit_code = 0; raw_response = '[{"id":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]'; want_absence = $false },
    @{ case_id = 'malformed-json'; exit_code = 0; raw_response = 'not-json: diagnostic survives'; want_absence = $false },
    @{ case_id = 'query-error'; exit_code = 7; raw_response = 'permission denied for exact filter'; want_absence = $false },
    @{ case_id = 'json-null'; exit_code = 0; raw_response = 'null'; want_absence = $false }
)
$results = [System.Collections.Generic.List[object]]::new()

foreach ($case in $cases) {
    $receipt = New-WslcCleanupReceipt -ContainerId $containerId -ExitCode $case.exit_code -RawOutput $case.raw_response
    if ($receipt.absence_verified -ne $case.want_absence) {
        throw "Unexpected absence classification for $($case.case_id)."
    }
    if ($receipt.container_id -ne $containerId -or $receipt.raw_response -cne $case.raw_response) {
        throw "The ID or original raw response was not retained for $($case.case_id)."
    }
    if ($receipt.query_exit_code -ne $case.exit_code) {
        throw "The query exit code was not retained for $($case.case_id)."
    }
    $results.Add([pscustomobject]@{
        case_id = $case.case_id
        container_id = $receipt.container_id
        query_exit_code = $receipt.query_exit_code
        raw_response = $receipt.raw_response
        absence_verified = $receipt.absence_verified
        reason = $receipt.reason
    })
}

$json = ConvertTo-Json -InputObject $results -Depth 4 -Compress
if ($OutputPath) {
    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
    $stream = [System.IO.File]::Open($resolvedOutput, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    try {
        $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($json + "`n")
        $stream.Write($bytes, 0, $bytes.Length)
    }
    finally {
        $stream.Dispose()
    }
}
Write-Output $json

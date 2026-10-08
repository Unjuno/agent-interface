$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'wslc_cleanup_receipt.psm1') -Force
$id = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
$cases = @(
    @{ exit_code = 0; raw = '[]'; verified = $true; reason = 'empty_array' },
    @{ exit_code = 0; raw = '[{}]'; verified = $false; reason = 'container_row_remains' },
    @{ exit_code = 0; raw = '{}'; verified = $false; reason = 'cleanup_response_shape_invalid' },
    @{ exit_code = 0; raw = 'false'; verified = $false; reason = 'cleanup_response_shape_invalid' },
    @{ exit_code = 0; raw = '0'; verified = $false; reason = 'cleanup_response_shape_invalid' },
    @{ exit_code = 0; raw = '"ok"'; verified = $false; reason = 'cleanup_response_shape_invalid' },
    @{ exit_code = 0; raw = 'null'; verified = $false; reason = 'json_null_is_not_empty_array' },
    @{ exit_code = 0; raw = 'not-json'; verified = $false; reason = 'cleanup_response_invalid' },
    @{ exit_code = 7; raw = 'query denied'; verified = $false; reason = 'scoped_query_failed' }
)
foreach ($case in $cases) {
    $receipt = New-WslcCleanupReceipt -ContainerId $id -ExitCode $case.exit_code -RawOutput $case.raw
    if ($receipt.absence_verified -ne $case.verified -or $receipt.reason -cne $case.reason) {
        throw "Unexpected result for '$($case.raw)': $($receipt | ConvertTo-Json -Compress)"
    }
    if ($receipt.raw_response -cne $case.raw) {
        throw "Raw response changed for '$($case.raw)'."
    }
}
Write-Output "PASS $($cases.Count) local classifier regression cases; no WSLc runtime invoked"

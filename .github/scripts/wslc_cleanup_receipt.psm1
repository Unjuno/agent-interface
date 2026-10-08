function New-WslcCleanupReceipt {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidatePattern('^[0-9a-fA-F]{64}$')]
        [string]$ContainerId,

        [Parameter(Mandatory = $true)]
        [int]$ExitCode,

        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$RawOutput
    )

    $verified = $false
    $reason = 'cleanup_response_invalid'
    $trimmed = $RawOutput.Trim()

    if ($ExitCode -ne 0) {
        $reason = 'scoped_query_failed'
    }
    elseif ([string]::IsNullOrWhiteSpace($trimmed)) {
        # WSLc 3.0.1 emits no stdout for a successful exact-ID zero-match query.
        $verified = $true
        $reason = 'empty_stdout'
    }
    elseif ($trimmed -match '^\[\s*\]
        $verified = $true
        $reason = 'empty_array'
    }
    else {
        try {
            $parsed = ConvertFrom-Json -InputObject $RawOutput -NoEnumerate -ErrorAction Stop
            if ($null -eq $parsed) {
                $reason = 'json_null_is_not_empty_array'
            }
            elseif ($parsed -is [array]) {
                $reason = 'container_row_remains'
            }
            else {
                $reason = 'cleanup_response_shape_invalid'
            }
        }
        catch {
            $reason = 'cleanup_response_invalid'
        }
    }

    [pscustomobject][ordered]@{
        container_id = $ContainerId
        query_exit_code = $ExitCode
        raw_response = $RawOutput
        absence_verified = $verified
        reason = $reason
    }
}

Export-ModuleMember -Function New-WslcCleanupReceipt

) {
        $verified = $true
        $reason = 'empty_array'
    }
    else {
        try {
            $parsed = ConvertFrom-Json -InputObject $RawOutput -NoEnumerate -ErrorAction Stop
            if ($null -eq $parsed) {
                $reason = 'json_null_is_not_empty_array'
            }
            elseif ($parsed -is [array]) {
                $reason = 'container_row_remains'
            }
            else {
                $reason = 'cleanup_response_shape_invalid'
            }
        }
        catch {
            $reason = 'cleanup_response_invalid'
        }
    }

    [pscustomobject][ordered]@{
        container_id = $ContainerId
        query_exit_code = $ExitCode
        raw_response = $RawOutput
        absence_verified = $verified
        reason = $reason
    }
}

Export-ModuleMember -Function New-WslcCleanupReceipt


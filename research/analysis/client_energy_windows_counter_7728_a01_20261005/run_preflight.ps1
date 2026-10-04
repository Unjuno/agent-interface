$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Add-Type -Path (Join-Path $scriptDir 'emi_probe.cs')
$slash = [string][char]92

$counterPath = $slash + 'Energy Meter(RAPL_Package0_PKG)' + $slash + 'Energy'
$startUtc = (Get-Date).ToUniversalTime().ToString('o')
$emiBefore = [EmiProbe]::ReadOnce()
$counterSample = Get-Counter -Counter $counterPath -MaxSamples 1 -ErrorAction Stop | Select-Object -ExpandProperty CounterSamples | Select-Object -First 1
$emiAfter = [EmiProbe]::ReadOnce()
$endUtc = (Get-Date).ToUniversalTime().ToString('o')

$hostPrefixPattern = '^' + $slash + $slash + $slash + $slash + '[^' + $slash + $slash + ']+' + $slash + $slash
$localHostPrefix = $slash + $slash + '<LOCAL_HOST>' + $slash
$sanitizedPath = $counterSample.Path -replace $hostPrefixPattern, $localHostPrefix
$raw = [pscustomobject]@{
    schema = 'issue7728-windows-energy-counter-a01-v1'
    start_utc = $startUtc
    end_utc = $endUtc
    host_os = [System.Environment]::OSVersion.Version.ToString()
    counter = [pscustomobject]@{
        requested_path = $counterPath
        returned_path = $sanitizedPath
        instance = $counterSample.InstanceName
        status = [string]$counterSample.Status
        timestamp_utc = $counterSample.Timestamp.ToUniversalTime().ToString('o')
        raw_value = [string]$counterSample.RawValue
        cooked_value = [string]$counterSample.CookedValue
        counter_type = [string]$counterSample.CounterType
        time_base = [string]$counterSample.TimeBase
    }
    emi_before = $emiBefore
    emi_after = $emiAfter
}
$raw | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $scriptDir 'raw-preflight.json') -Encoding utf8
Write-Output (Get-Content -Raw -LiteralPath (Join-Path $scriptDir 'raw-preflight.json'))

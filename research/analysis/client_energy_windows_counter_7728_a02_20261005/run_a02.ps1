$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Add-Type -Path (Join-Path $scriptDir 'emi_probe.cs')
$slash = [string][char]92
$energyPath = $slash + 'Energy Meter(RAPL_Package0_PKG)' + $slash + 'Energy'
$cpuPath = $slash + 'Processor(_Total)' + $slash + '% Processor Time'
$startUtc = (Get-Date).ToUniversalTime().ToString('o')
$emiBefore = [EmiProbe]::ReadOnce()
$samples = Get-Counter -Counter @($energyPath, $cpuPath) -SampleInterval 1 -MaxSamples 6 -ErrorAction Stop | Select-Object -ExpandProperty CounterSamples
$emiAfter = [EmiProbe]::ReadOnce()
$endUtc = (Get-Date).ToUniversalTime().ToString('o')

$hostPrefixPattern = '^' + $slash + $slash + $slash + $slash + '[^' + $slash + $slash + ']+' + $slash + $slash
$localHostPrefix = $slash + $slash + '<LOCAL_HOST>' + $slash
function Convert-Sample($sample) {
    [pscustomobject]@{
        returned_path = ($sample.Path -replace $hostPrefixPattern, $localHostPrefix)
        instance = $sample.InstanceName
        status = [string]$sample.Status
        timestamp_utc = $sample.Timestamp.ToUniversalTime().ToString('o')
        raw_value = [string]$sample.RawValue
        cooked_value = [string]$sample.CookedValue
        counter_type = [string]$sample.CounterType
        time_base = [string]$sample.TimeBase
    }
}
$energySamples = @($samples | Where-Object { $_.Path -match 'Energy Meter\(RAPL_Package0_PKG\)\\Energy$' } | Sort-Object Timestamp | ForEach-Object { Convert-Sample $_ })
$cpuSamples = @($samples | Where-Object { $_.Path -match 'Processor\(_Total\)\\% Processor Time$' } | Sort-Object Timestamp | ForEach-Object { Convert-Sample $_ })
$raw = [pscustomobject]@{
    schema = 'issue7728-windows-energy-counter-a02-v1'
    start_utc = $startUtc
    end_utc = $endUtc
    host_os = [System.Environment]::OSVersion.Version.ToString()
    energy_samples = $energySamples
    cpu_samples = $cpuSamples
    emi_before = $emiBefore
    emi_after = $emiAfter
}
$raw | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $scriptDir 'raw-a02.json') -Encoding utf8
Write-Output (Get-Content -Raw -LiteralPath (Join-Path $scriptDir 'raw-a02.json'))

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'gate_correction/gpu_preflight_gate.ps1')
$rawDir = Join-Path $PSScriptRoot 'raw'
New-Item -ItemType Directory -Force -Path $rawDir | Out-Null
$gate = Invoke-GpuLeasePreflight
$gateRecord = [pscustomobject]@{
    observed_utc = [DateTime]::UtcNow.ToString('o')
    gate = $gate
    candidate_invocations_before_gate = 0
}
$gateJson = $gateRecord | ConvertTo-Json -Depth 8 -Compress
[System.IO.File]::WriteAllText((Join-Path $rawDir 'preflight.json'), $gateJson, [System.Text.UTF8Encoding]::new($false))
if ($gate.status -ne 'PREFLIGHT_OK') {
    Write-Output ($gateRecord | ConvertTo-Json -Depth 8 -Compress)
    exit 20
}
$captureOutput = & py -3.11 -B (Join-Path $PSScriptRoot 'run_capture.py')
$captureExit = $LASTEXITCODE
$captureOutput | Set-Content -LiteralPath (Join-Path $rawDir 'launcher.stdout.txt') -Encoding utf8
if ($captureExit -ne 0) {
    Write-Output ($captureOutput -join [Environment]::NewLine)
    exit 21
}
if (-not (Test-Path -LiteralPath (Join-Path $rawDir 'candidate.json'))) {
    Write-Output '{"status":"STOP_DURABLE_RAW_MISSING"}'
    exit 22
}
if (-not (Test-Path -LiteralPath (Join-Path $rawDir 'publication_receipt.json'))) {
    Write-Output '{"status":"STOP_PUBLICATION_RECEIPT_MISSING"}'
    exit 23
}
Write-Output ($captureOutput -join [Environment]::NewLine)
exit 0

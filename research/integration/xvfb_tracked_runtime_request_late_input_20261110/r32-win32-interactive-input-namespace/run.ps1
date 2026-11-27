$ErrorActionPreference = 'Stop'
$runDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$evidenceDirectory = Join-Path $runDirectory 'evidence'
New-Item -ItemType Directory -Force -Path $evidenceDirectory | Out-Null
$pythonPath = (Get-Command python -ErrorAction Stop).Source
$pythonVersion = & $pythonPath -c "import sys; print(sys.version)"
& $pythonPath (Join-Path $runDirectory 'probe.py') 1> (Join-Path $evidenceDirectory 'result.json') 2> (Join-Path $evidenceDirectory 'stderr.log')
$probeExit = $LASTEXITCODE
$receipt = [ordered]@{
    probe_exit_code = $probeExit
    python_path = $pythonPath
    python_version = $pythonVersion
    finished_utc = [DateTime]::UtcNow.ToString('o')
}
$receipt | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 (Join-Path $evidenceDirectory 'RUN_EXIT.json')
exit $probeExit

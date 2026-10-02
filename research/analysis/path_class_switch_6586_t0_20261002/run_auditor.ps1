param()
$ErrorActionPreference = 'Stop'
$packageRoot = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $packageRoot '..\..\..')).Path
$freeze = Get-Content -Raw (Join-Path $packageRoot 'FREEZE.json') | ConvertFrom-Json
$base = (& git -C $repoRoot rev-parse origin/main).Trim()
if ($base -ne $freeze.base_main_sha) { throw "STOP_MAIN_CHANGED expected=$($freeze.base_main_sha) actual=$base" }
foreach ($entry in $freeze.hashes.PSObject.Properties) {
    $file = Join-Path $packageRoot $entry.Name
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash.ToLowerInvariant()
    if ($actual -ne $entry.Value) { throw "STOP_SOURCE_HASH $($entry.Name) expected=$($entry.Value) actual=$actual" }
}
$image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$imageListing = (& wslc.exe images --digests | Out-String)
if ($imageListing -notmatch [regex]::Escape('sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f')) { throw 'STOP_PINNED_IMAGE_NOT_CACHED' }
$raw = Join-Path $packageRoot 'results\formal-01\candidate'
if (-not (Test-Path -LiteralPath (Join-Path $raw 'candidate.raw.json'))) { throw 'STOP_CANDIDATE_RAW_MISSING' }
if ((Get-Content -Raw (Join-Path $packageRoot 'results\formal-01\candidate.exitcode.txt')).Trim() -ne '0') { throw 'STOP_CANDIDATE_NOT_EXIT_ZERO' }
$outDir = Join-Path $packageRoot 'results\formal-01\auditor'
if (-not (Test-Path -LiteralPath $outDir)) { throw 'STOP_AUDITOR_OUTPUT_DIRECTORY_MISSING' }
if ((Get-ChildItem -LiteralPath $outDir -Force | Measure-Object).Count -ne 0) { throw 'STOP_AUDITOR_OUTPUT_NOT_EMPTY' }
$stdout = Join-Path $packageRoot 'results\formal-01\auditor.stdout.txt'
$exitFile = Join-Path $packageRoot 'results\formal-01\auditor.exitcode.txt'
if ((Test-Path -LiteralPath $stdout) -or (Test-Path -LiteralPath $exitFile)) { throw 'STOP_AUDITOR_ALREADY_INVOKED' }
$arguments = @('run','--rm','--pull','never','--network','none','--cpus','0.25','--memory','512M','--user','65534:65534','--mount',"type=bind,source=$packageRoot,target=/src,readonly",'--mount',"type=bind,source=$raw,target=/raw,readonly",'--mount',"type=bind,source=$outDir,target=/out",'--workdir','/src',$image,'python','-B','/src/audit.py','--input','/src/inputs.json','--oracle','/src/oracle.json','--raw','/raw/candidate.raw.json','--output','/out/audit.json')
& wslc.exe @arguments 2>&1 | Tee-Object -FilePath $stdout
$code = $LASTEXITCODE
Set-Content -LiteralPath $exitFile -Value $code -Encoding ascii
if ($code -ne 0) { throw "STOP_AUDITOR_EXIT_$code" }



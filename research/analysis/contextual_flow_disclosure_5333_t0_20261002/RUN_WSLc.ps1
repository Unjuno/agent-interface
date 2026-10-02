param(
    [Parameter(Mandatory = $true)]
    [string]$PackagePath
)

$ErrorActionPreference = 'Stop'
$runtime = 'C:\Program Files\WSL\wslc.exe'
$image = 'sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4'
$package = (Resolve-Path -LiteralPath $PackagePath).Path
$runDir = Join-Path $package 'run'

if (-not (Test-Path -LiteralPath $runtime -PathType Leaf)) { throw 'Pinned local wslc.exe is unavailable.' }
if (Test-Path -LiteralPath $runDir) { throw 'run/ already exists; refusing to overwrite formal outputs.' }
New-Item -ItemType Directory -Path $runDir | Out-Null
$sourceMount = "${package}:/src:ro"
$outputMount = "${runDir}:/out:rw"

& $runtime run --pull never --network none --cpus 1 --memory 256m --user 1000 --rm --name cfd5333-t0-candidate --volume $sourceMount --volume $outputMount --workdir /src $image python candidate.py --out /out/candidate.json
if ($LASTEXITCODE -ne 0) { throw "Candidate exited $LASTEXITCODE; allocation is terminal and auditor must not run." }

& $runtime run --pull never --network none --cpus 1 --memory 256m --user 1000 --rm --name cfd5333-t0-auditor --volume $sourceMount --volume $outputMount --workdir /src $image python auditor.py --candidate /out/candidate.json --out /out/audit.json
if ($LASTEXITCODE -ne 0) { throw "Independent auditor exited $LASTEXITCODE; allocation is terminal and must not be retried." }

Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $runDir 'candidate.json'), (Join-Path $runDir 'audit.json') | Format-Table -AutoSize

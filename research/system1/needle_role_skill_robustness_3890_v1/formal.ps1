param(
    [Parameter(Mandatory=$true)][string]$OutRoot
)
$ErrorActionPreference = "Stop"
$sourceRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$image = "needle-pilot05:local"
$expectedImage = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
$seeds = @(100000,100100,100200,100300,100400,100500,100600,100700,100800,100900)
$phase = "preflight"
$currentSeed = $null
if (Test-Path -LiteralPath $OutRoot) {
    if (@(Get-ChildItem -LiteralPath $OutRoot -Force).Count -ne 0) { throw "formal output directory must be empty" }
} else {
    New-Item -ItemType Directory -Path $OutRoot | Out-Null
}
$OutRoot = (Resolve-Path -LiteralPath $OutRoot).Path
$sourceMount = $sourceRoot.Replace("","/")
$outMount = $OutRoot.Replace("","/")
function Assert-Image {
    $id = (& docker image inspect $image --format "{{.Id}}" 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $id -ne $expectedImage) { throw "pinned Docker image unavailable or mismatched: $id" }
}
function Invoke-Container([string[]]$Arguments,[string]$LogPath) {
    & docker @Arguments 2>&1 | Tee-Object -FilePath $LogPath
    if ($LASTEXITCODE -ne 0) { throw "docker exit $LASTEXITCODE; see $LogPath" }
}
try {
    Assert-Image
    $freeze = Get-Content -Raw -LiteralPath (Join-Path $sourceRoot "FREEZE.json") | ConvertFrom-Json
    if ($freeze.seeds.Count -ne 10 -or (@($freeze.seeds) -join ",") -ne ($seeds -join ",")) { throw "seed schedule differs from freeze" }
    foreach ($property in $freeze.source_sha256.PSObject.Properties) {
        $file = Join-Path $sourceRoot $property.Name
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash.ToLowerInvariant()
        if ($actual -ne $property.Value) { throw "frozen source hash mismatch: $($property.Name)" }
    }
    $phase = "formal"
    foreach ($seed in $seeds) {
        $currentSeed = $seed
        $seedRoot = Join-Path $OutRoot "seed-$seed"
        $builder = Join-Path $seedRoot "builder"
        $load1 = Join-Path $seedRoot "load1"
        $load2 = Join-Path $seedRoot "load2"
        New-Item -ItemType Directory -Force -Path $builder,$load1,$load2 | Out-Null
        $common = @("--rm","--pull=never","--platform","linux/amd64","--network","none","--read-only",
            "--tmpfs","/tmp:rw,nosuid,nodev,size=64m","--pids-limit","64","--memory","2g","--cpus","1",
            "--mount","type=bind,source=$sourceMount,target=/src,readonly","--workdir","/src",$image)
        $b = $builder.Replace("","/")
        $phase = "builder-$seed"
        $dockerArgs = @($common[0..($common.Count-2)]) + @("--env","NEEDLE_SEED=$seed","--env","NEEDLE_OUTPUT=/out",
            "--mount","type=bind,source=$b,target=/out","$image","-B","runner.py")
        Invoke-Container $dockerArgs (Join-Path $seedRoot "builder.stdout.log")
        foreach ($name in @("skill.json","expected.json","builder_meta.json")) {
            if (-not (Test-Path -LiteralPath (Join-Path $builder $name))) { throw "builder omitted $name for seed $seed" }
        }
        foreach ($loaderName in @("load1","load2")) {
            $loadOut = Join-Path $seedRoot $loaderName
            $loadOutMount = $loadOut.Replace("","/")
            $phase = "$loaderName-$seed"
            $dockerArgs = @("--rm","--pull=never","--platform","linux/amd64","--network","none","--read-only",
                "--tmpfs","/tmp:rw,nosuid,nodev,size=64m","--pids-limit","64","--memory","2g","--cpus","1",
                "--mount","type=bind,source=$sourceMount,target=/src,readonly",
                "--mount","type=bind,source=$b,target=/package,readonly",
                "--mount","type=bind,source=$loadOutMount,target=/out","--workdir","/src",$image,
                "-B","loader.py","/package/skill.json","/package/expected.json","/out/loader.json")
            Invoke-Container $dockerArgs (Join-Path $seedRoot "$loaderName.stdout.log")
            if (-not (Test-Path -LiteralPath (Join-Path $loadOut "loader.json"))) { throw "loader omitted output for seed $seed" }
        }
    }
    $phase = "independent-audit"
    $dockerArgs = @("--rm","--pull=never","--platform","linux/amd64","--network","none","--read-only",
        "--tmpfs","/tmp:rw,nosuid,nodev,size=64m","--pids-limit","64","--memory","2g","--cpus","1",
        "--mount","type=bind,source=$sourceMount,target=/src,readonly",
        "--mount","type=bind,source=$outMount,target=/evidence",
        "--workdir","/src",$image,"-B","audit.py","/evidence")
    Invoke-Container $dockerArgs (Join-Path $OutRoot "audit.stdout.log")
    $result = Get-Content -Raw -LiteralPath (Join-Path $OutRoot "audit.json") | ConvertFrom-Json
    if ($result.audit -ne "PASS") { throw "independent audit failed: $($result.disposition)" }
    Write-Output ("FORMAL_COMPLETE " + $result.disposition)
} catch {
    $stop = [ordered]@{status="STOP";phase=$phase;seed=$currentSeed;message=$_.Exception.Message;no_retry=$true}
    $stopPath = Join-Path $OutRoot "STOP.json"
    if (-not (Test-Path -LiteralPath $stopPath)) {
        $stop | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $stopPath -Encoding utf8
    }
    Write-Error ("FORMAL_STOP phase={0} seed={1} no_retry=true: {2}" -f $phase,$currentSeed,$_.Exception.Message)
    exit 1
}

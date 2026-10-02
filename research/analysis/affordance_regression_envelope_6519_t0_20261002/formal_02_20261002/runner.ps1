param(
    [Parameter(Mandatory=$true)][ValidateSet('construction','candidate','auditor')][string]$Stage,
    [switch]$DryRun,
    [switch]$Run
)

$ErrorActionPreference = 'Stop'
if (($DryRun.IsPresent -and $Run.IsPresent) -or (-not $DryRun.IsPresent -and -not $Run.IsPresent)) {
    throw 'Specify exactly one of -DryRun or -Run.'
}

$stageRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$packageRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $stageRoot)).Path
$formalRoot = Join-Path $packageRoot 'formal_02_20261002'
$frozenImage = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$sourceRoot = switch ($Stage) {
    'construction' { $packageRoot }
    'candidate' { Join-Path $packageRoot 'formal_01_20261002/candidate_source' }
    'auditor' { Join-Path $packageRoot 'formal_01_20261002/audit_source' }
}
$sourceRoot = (Resolve-Path -LiteralPath $sourceRoot).Path
$outputName = switch ($Stage) {
    'construction' { 'construction' }
    'candidate' { 'candidate_output' }
    'auditor' { 'audit_output' }
}
$outputRoot = Join-Path $formalRoot $outputName
if (-not [IO.Path]::IsPathFullyQualified($packageRoot) -or -not [IO.Path]::IsPathFullyQualified($sourceRoot) -or -not [IO.Path]::IsPathFullyQualified($outputRoot)) {
    throw 'Refusing WSLc invocation: package, source, and output paths must be absolute.'
}
if (-not (Test-Path -LiteralPath $outputRoot -PathType Container)) { throw "Missing stage output directory: $outputRoot" }
if ((Get-ChildItem -LiteralPath $outputRoot -Force).Count -ne 0) { throw "Stage output is not fresh: $outputRoot" }

$inputRoot = $null
if ($Stage -eq 'auditor') {
    $inputRoot = Join-Path $formalRoot 'audit_input'
    if (-not (Test-Path -LiteralPath $inputRoot -PathType Container)) { throw "Missing auditor input directory: $inputRoot" }
    if ($Run.IsPresent) {
        $candidateRaw = Join-Path $formalRoot 'candidate_output/candidate.raw.json'
        $auditRaw = Join-Path $inputRoot 'candidate.raw.json'
        if (-not (Test-Path -LiteralPath $candidateRaw -PathType Leaf) -or -not (Test-Path -LiteralPath $auditRaw -PathType Leaf)) {
            throw 'Auditor requires both the retained candidate raw and its audit-input copy.'
        }
        $candidateHash = (Get-FileHash -LiteralPath $candidateRaw -Algorithm SHA256).Hash
        $auditHash = (Get-FileHash -LiteralPath $auditRaw -Algorithm SHA256).Hash
        if ($candidateHash -ne $auditHash) { throw 'Candidate raw and audit-input copy hashes differ.' }
    }
}

$containerName = switch ($Stage) {
    'construction' { 'affordance-6519-t0b-construction' }
    'candidate' { 'affordance-6519-t0b-candidate' }
    'auditor' { 'affordance-6519-t0b-auditor' }
}
$inner = switch ($Stage) {
    'construction' { @('python','-B','-m','unittest','-v','test_protocol') }
    'candidate' { @('python','-B','/src/candidate.py','/src/fixture.json','/out/candidate.raw.json') }
    'auditor' { @('python','-B','/src/auditor.py','/src/fixture.json','/src/oracle.json','/in/candidate.raw.json','/out/audit.json') }
}
$argsForWslc = @(
    'run','--pull','never','--network','none','--cpus','1','--memory','1G','--user','65534:65534',
    '--name',$containerName,
    '--mount',("type=bind,source={0},target=/src,readonly" -f $sourceRoot)
)
if ($Stage -eq 'auditor') {
    $argsForWslc += @('--mount',("type=bind,source={0},target=/in,readonly" -f $inputRoot))
}
$argsForWslc += @('--mount',("type=bind,source={0},target=/out" -f $outputRoot),'--workdir','/src',$frozenImage)
$argsForWslc += $inner

foreach ($arg in $argsForWslc) {
    if ($null -eq $arg -or $arg -match 'source=,') { throw 'Refusing WSLc invocation: an argument is null or a mount source is empty.' }
}
$plan = [ordered]@{
    stage = $Stage
    package_root = $packageRoot
    source_root = $sourceRoot
    input_root = $inputRoot
    output_root = $outputRoot
    container_name = $containerName
    image = $frozenImage
    arguments = $argsForWslc
}
if ($DryRun.IsPresent) {
    $plan | ConvertTo-Json -Depth 6
    exit 0
}

$stdoutPath = Join-Path $outputRoot 'stdout.log'
$stderrPath = Join-Path $outputRoot 'stderr.log'
$runPath = Join-Path $outputRoot 'RUN.json'
$started = [DateTime]::UtcNow.ToString('o')
& wslc.exe @argsForWslc 1> $stdoutPath 2> $stderrPath
$exitCode = $LASTEXITCODE
$finished = [DateTime]::UtcNow.ToString('o')
$runRecord = [ordered]@{
    stage = $Stage
    container_name = $containerName
    image = $frozenImage
    package_root = $packageRoot
    source_root = $sourceRoot
    input_root = $inputRoot
    output_root = $outputRoot
    command = ($argsForWslc -join ' ')
    started_at_utc = $started
    finished_at_utc = $finished
    exit_code = $exitCode
}
$runRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $runPath -Encoding utf8NoBOM
$exitCode | Set-Content -LiteralPath (Join-Path $outputRoot 'exit.txt') -Encoding ascii
exit $exitCode

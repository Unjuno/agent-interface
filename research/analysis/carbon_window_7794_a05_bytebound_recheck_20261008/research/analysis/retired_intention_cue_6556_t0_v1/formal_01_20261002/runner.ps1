param(
    [Parameter(Mandatory=$true)][ValidateSet('construction','candidate','auditor')][string]$Stage,
    [switch]$DryRun,
    [switch]$Run
)

$ErrorActionPreference = 'Stop'
if (($DryRun.IsPresent -and $Run.IsPresent) -or (-not $DryRun.IsPresent -and -not $Run.IsPresent)) { throw 'Specify exactly one of -DryRun or -Run.' }
$cli = Get-Command wslc.exe -ErrorAction Stop
if (-not $cli.Source -or -not [IO.Path]::IsPathFullyQualified($cli.Source)) { throw 'wslc.exe must resolve to a fully qualified executable path.' }
$cliVersion = (& $cli.Source --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Unable to read WSLc version: $cliVersion" }
$formal = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$package = (Resolve-Path -LiteralPath (Split-Path -Parent $formal)).Path
$image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$source = switch ($Stage) {
    'construction' { $package }
    'candidate' { Join-Path $formal 'candidate_source' }
    'auditor' { Join-Path $formal 'audit_source' }
}
$source = (Resolve-Path -LiteralPath $source).Path
$outName = switch ($Stage) { 'construction' { 'construction' } 'candidate' { 'candidate_output' } 'auditor' { 'audit_output' } }
$out = Join-Path $formal $outName
if (-not [IO.Path]::IsPathFullyQualified($source) -or -not [IO.Path]::IsPathFullyQualified($out)) { throw 'All bind paths must be absolute.' }
if (-not (Test-Path -LiteralPath $out -PathType Container) -or (Get-ChildItem -LiteralPath $out -Force).Count -ne 0) { throw "Output must exist and be fresh: $out" }
$input = $null
if ($Stage -eq 'auditor') {
    $input = Join-Path $formal 'audit_input'
    $raw = Join-Path $formal 'candidate_output/candidate.raw.json'
    $copy = Join-Path $input 'candidate.raw.json'
    if (-not (Test-Path -LiteralPath $raw -PathType Leaf) -or -not (Test-Path -LiteralPath $copy -PathType Leaf)) { throw 'Auditor input/raw missing.' }
    if ((Get-FileHash $raw -Algorithm SHA256).Hash -ne (Get-FileHash $copy -Algorithm SHA256).Hash) { throw 'Auditor input is not byte-identical.' }
}
$name = "retired-cue-6556-t0-$Stage"
$inner = switch ($Stage) {
    'construction' { @('python','-B','-m','unittest','-v','test_protocol') }
    'candidate' { @('python','-B','/src/candidate.py','/src/fixture.json','/out/candidate.raw.json') }
    'auditor' { @('python','-B','/src/auditor.py','/src/fixture.json','/src/oracle.json','/in/candidate.raw.json','/out/audit.json') }
}
$argsForWslc = @('run','--pull','never','--network','none','--cpus','1','--memory','1G','--user','65534:65534','--name',$name,'--mount',("type=bind,source={0},target=/src,readonly" -f $source))
if ($Stage -eq 'auditor') { $argsForWslc += @('--mount',("type=bind,source={0},target=/in,readonly" -f $input)) }
$argsForWslc += @('--mount',("type=bind,source={0},target=/out" -f $out),'--workdir','/src',$image)
$argsForWslc += $inner
foreach ($arg in $argsForWslc) { if ($null -eq $arg -or $arg -match 'source=,') { throw 'Empty or null WSLc argument.' } }
if ($DryRun.IsPresent) { [ordered]@{stage=$Stage;cli=$cli.Source;cli_version=$cliVersion;source=$source;input=$input;output=$out;container=$name;image=$image;arguments=$argsForWslc} | ConvertTo-Json -Depth 5; exit 0 }
$started=[DateTime]::UtcNow.ToString('o')
& $cli.Source @argsForWslc 1> (Join-Path $out 'stdout.log') 2> (Join-Path $out 'stderr.log')
$code=$LASTEXITCODE
$record=[ordered]@{stage=$Stage;cli=$cli.Source;cli_version=$cliVersion;container=$name;image=$image;source=$source;input=$input;output=$out;command=($argsForWslc -join ' ');started_at_utc=$started;finished_at_utc=[DateTime]::UtcNow.ToString('o');exit_code=$code}
$record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'RUN.json') -Encoding utf8NoBOM
$code | Set-Content -LiteralPath (Join-Path $out 'exit.txt') -Encoding ascii
exit $code

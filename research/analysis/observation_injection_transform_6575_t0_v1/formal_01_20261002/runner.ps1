param(
    [Parameter(Mandatory=$true)][ValidateSet('construction','candidate','auditor')][string]$Stage,
    [switch]$DryRun,
    [switch]$Run
)
$ErrorActionPreference = 'Stop'
if (($DryRun.IsPresent -and $Run.IsPresent) -or (-not $DryRun.IsPresent -and -not $Run.IsPresent)) { throw 'Specify exactly one of -DryRun or -Run.' }
$cli = Get-Command wslc.exe -ErrorAction Stop
if (-not $cli.Source -or -not [IO.Path]::IsPathFullyQualified($cli.Source)) { throw 'WSLc executable path must be absolute.' }
$version = (& $cli.Source --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Could not read WSLc version: $version" }
$formal = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$package = (Resolve-Path -LiteralPath (Split-Path -Parent $formal)).Path
$freeze = Get-Content -LiteralPath (Join-Path $formal 'FREEZE.json') -Raw | ConvertFrom-Json
foreach ($entry in $freeze.files.PSObject.Properties) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $package $entry.Name) -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $entry.Value) { throw "Frozen source changed: $($entry.Name)" }
}
foreach ($entry in $freeze.staged_sources.PSObject.Properties) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $formal $entry.Name) -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $entry.Value) { throw "Staged source changed: $($entry.Name)" }
}
$source = switch ($Stage) { 'construction' {$package} 'candidate' {(Join-Path $formal 'candidate_source')} 'auditor' {(Join-Path $formal 'audit_source')} }
$source = (Resolve-Path -LiteralPath $source).Path
$outName = switch ($Stage) { 'construction' {'construction'} 'candidate' {'candidate_output'} 'auditor' {'audit_output'} }
$out = Join-Path $formal $outName
if ((Get-ChildItem -LiteralPath $out -Force).Count -ne 0) { throw "Output is not fresh: $out" }
$name = "obs-injection-6575-t0-$Stage"
$input = $null
$inner = switch ($Stage) {
    'construction' { @('python','-B','-m','unittest','-v','test_protocol') }
    'candidate' { @('python','-B','/src/candidate.py','/out/candidate.raw.json') }
    'auditor' { @('python','-B','/src/auditor.py','/src/oracle.json','/in/candidate.raw.json','/out/audit.json') }
}
$argsForWslc = @('run','--pull','never','--network','none','--cpus','1','--memory','1G','--user','65534:65534','--name',$name,'--mount',("type=bind,source={0},target=/src,readonly" -f $source))
if ($Stage -eq 'auditor') {
    $input = Join-Path $formal 'audit_input'
    $raw = Join-Path $formal 'candidate_output/candidate.raw.json'
    $copy = Join-Path $input 'candidate.raw.json'
    if (-not (Test-Path -LiteralPath $raw -PathType Leaf) -or -not (Test-Path -LiteralPath $copy -PathType Leaf)) { throw 'Auditor raw input/copy missing.' }
    if ((Get-FileHash $raw -Algorithm SHA256).Hash -ne (Get-FileHash $copy -Algorithm SHA256).Hash) { throw 'Auditor input is not byte-identical.' }
    $argsForWslc += @('--mount',("type=bind,source={0},target=/in,readonly" -f $input))
}
$argsForWslc += @('--mount',("type=bind,source={0},target=/out" -f $out),'--workdir','/src',$freeze.runtime.image)
$argsForWslc += $inner
if ($DryRun.IsPresent) { [ordered]@{stage=$Stage;cli=$cli.Source;version=$version;source=$source;input=$input;output=$out;image=$freeze.runtime.image;arguments=$argsForWslc} | ConvertTo-Json -Depth 5; exit 0 }
$start = [DateTime]::UtcNow.ToString('o')
& $cli.Source @argsForWslc 1> (Join-Path $out 'stdout.log') 2> (Join-Path $out 'stderr.log')
$code = $LASTEXITCODE
[ordered]@{stage=$Stage;cli=$cli.Source;version=$version;container=$name;image=$freeze.runtime.image;source=$source;input=$input;output=$out;command=($argsForWslc -join ' ');started_at_utc=$start;finished_at_utc=[DateTime]::UtcNow.ToString('o');exit_code=$code} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'RUN.json') -Encoding utf8NoBOM
$code | Set-Content -LiteralPath (Join-Path $out 'exit.txt') -Encoding ascii
exit $code

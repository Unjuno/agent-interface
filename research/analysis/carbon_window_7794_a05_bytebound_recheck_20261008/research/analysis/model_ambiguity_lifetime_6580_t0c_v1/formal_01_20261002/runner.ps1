param([Parameter(Mandatory=$true)][ValidateSet('construction','candidate','auditor')][string]$Stage,[switch]$Run)
$ErrorActionPreference='Stop'
if (-not $Run) { throw 'Formal runner requires -Run; dry-run is not a formal invocation.' }
$cli=(Get-Command wslc.exe -ErrorAction Stop).Source
$formal=(Resolve-Path -LiteralPath $PSScriptRoot).Path
$package=(Resolve-Path -LiteralPath (Split-Path -Parent $formal)).Path
$freeze=Get-Content -LiteralPath (Join-Path $formal 'FREEZE.json') -Raw | ConvertFrom-Json
foreach($entry in $freeze.files.PSObject.Properties){$actual=(Get-FileHash (Join-Path $package $entry.Name) -Algorithm SHA256).Hash.ToLower();if($actual -ne $entry.Value){throw "Frozen source changed: $($entry.Name)"}}
foreach($entry in $freeze.staged_sources.PSObject.Properties){$actual=(Get-FileHash (Join-Path $formal $entry.Name) -Algorithm SHA256).Hash.ToLower();if($actual -ne $entry.Value){throw "Frozen staged source changed: $($entry.Name)"}}
$image=$freeze.runtime.image
$outputName=switch($Stage){construction{'construction'} candidate{'candidate_output'} auditor{'audit_output'}}
$out=Join-Path $formal $outputName
if((Get-ChildItem -LiteralPath $out -Force).Count -ne 0){throw "Output is not fresh: $out"}
$source=switch($Stage){construction{$package} candidate{Join-Path $formal 'candidate_source'} auditor{Join-Path $formal 'audit_source'}}
$inner=switch($Stage){construction{@('python','-B','-m','unittest','-v','test_protocol')} candidate{@('python','-B','/src/candidate.py','/out/candidate.raw.json')} auditor{@('python','-B','/src/auditor.py','/in/candidate.raw.json','/out/audit.json')}}
$argsForWslc=@('run','--pull','never','--network','none','--cpus','1','--memory','1G','--user','65534:65534','--name',"issue-6580-t0c-$Stage",'--mount',("type=bind,source={0},target=/src,readonly" -f $source))
$input=$null
if($Stage -eq 'auditor'){$input=Join-Path $formal 'audit_input';$raw=Join-Path $formal 'candidate_output/candidate.raw.json';$copy=Join-Path $input 'candidate.raw.json';if(-not(Test-Path $raw -PathType Leaf)-or -not(Test-Path $copy -PathType Leaf)){throw 'Auditor input missing.'};if((Get-FileHash $raw -Algorithm SHA256).Hash -ne (Get-FileHash $copy -Algorithm SHA256).Hash){throw 'Auditor input is not byte-identical.'};$argsForWslc+=@('--mount',("type=bind,source={0},target=/in,readonly" -f $input))}
$argsForWslc+=@('--mount',("type=bind,source={0},target=/out" -f $out),'--workdir','/src',$image)+$inner
$started=[DateTime]::UtcNow.ToString('o')
& $cli @argsForWslc 1> (Join-Path $out 'stdout.log') 2> (Join-Path $out 'stderr.log')
$code=$LASTEXITCODE
[ordered]@{stage=$Stage;cli=$cli;version=(& $cli --version 2>&1 | Out-String).Trim();image=$image;input=$input;output=$out;command=($argsForWslc -join ' ');started_at_utc=$started;finished_at_utc=[DateTime]::UtcNow.ToString('o');exit_code=$code}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $out 'RUN.json') -Encoding utf8NoBOM
$code|Set-Content (Join-Path $out 'exit.txt') -Encoding ascii
exit $code

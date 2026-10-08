param([Parameter(Mandatory=$true)][ValidateSet('construction','candidate','auditor')][string]$Stage,[switch]$Run)
$ErrorActionPreference='Stop'
if(-not $Run){throw 'Formal runner requires -Run.'}
$cli=(Get-Command wslc.exe -ErrorAction Stop).Source
$formal=(Resolve-Path -LiteralPath $PSScriptRoot).Path
$package=(Resolve-Path -LiteralPath (Split-Path -Parent $formal)).Path
$freeze=Get-Content -LiteralPath (Join-Path $formal 'FREEZE.json') -Raw | ConvertFrom-Json
$repoRoot=(& git -C $package rev-parse --show-toplevel).Trim()
$remoteMain=(& git -C $repoRoot rev-parse origin/main).Trim()
if($remoteMain -ne $freeze.base_main){throw "origin/main moved after freeze: $remoteMain"}
$branch=(& git -C $repoRoot branch --show-current).Trim()
if($branch -ne $freeze.branch){throw "Unexpected branch: $branch"}
$version=(& $cli --version 2>&1 | Out-String).Trim()
if($version -ne $freeze.runtime.version){throw "Unexpected WSLc version: $version"}
& $cli image inspect $freeze.runtime.image 1>$null 2>$null
if($LASTEXITCODE -ne 0){throw 'Frozen image is not available locally'}
foreach($e in $freeze.files.PSObject.Properties){$h=(Get-FileHash -LiteralPath (Join-Path $package $e.Name) -Algorithm SHA256).Hash.ToLower();if($h -ne $e.Value){throw "Frozen source mismatch: $($e.Name)"}}
foreach($e in $freeze.contract_sources.PSObject.Properties){$p=Join-Path $repoRoot $e.Name;$h=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower();if($h -ne $e.Value.sha256){throw "Contract source hash mismatch: $($e.Name)"};$blob=(& git -C $repoRoot rev-parse "$($freeze.base_main):$($e.Name)" 2>$null).Trim();if($blob -ne $e.Value.blob){throw "Contract Git blob mismatch: $($e.Name)"}}
foreach($e in $freeze.staged_sources.PSObject.Properties){$h=(Get-FileHash -LiteralPath (Join-Path $formal $e.Name) -Algorithm SHA256).Hash.ToLower();if($h -ne $e.Value){throw "Staged source mismatch: $($e.Name)"}}
$rh=(Get-FileHash -LiteralPath (Join-Path $formal 'runner.ps1') -Algorithm SHA256).Hash.ToLower();if($rh -ne $freeze.runner_sha256){throw 'Frozen runner mismatch'}
$ph=(Get-FileHash -LiteralPath (Join-Path $formal 'PREREGISTRATION.md') -Algorithm SHA256).Hash.ToLower();if($ph -ne $freeze.preregistration_sha256){throw 'Frozen preregistration mismatch'}
$outName=switch($Stage){construction{'construction'} candidate{'candidate_output'} auditor{'audit_output'}}
$out=Join-Path $formal $outName
if((Get-ChildItem -LiteralPath $out -Force).Count -ne 0){throw "Output is not fresh: $out"}
$source=switch($Stage){construction{Join-Path $formal 'construction_source'} candidate{Join-Path $formal 'candidate_source'} auditor{Join-Path $formal 'audit_source'}}
$inner=switch($Stage){construction{@('python','-B','-m','unittest','-v','test_protocol')} candidate{@('python','-B','/src/candidate.py','/src/cases.json','/out/raw.json')} auditor{@('python','-B','/src/auditor.py','/src/cases.json','/in/raw.json','/out/audit.json')}}
$argsW=@('run','--pull','never','--network','none','--cpus','1','--memory','512M','--user','65534:65534','--name',"issue-6561-t0b-$Stage",'--mount',("type=bind,source={0},target=/src,readonly" -f $source))
$input=$null
if($Stage -eq 'auditor'){$input=Join-Path $formal 'audit_input';$raw=Join-Path $formal 'candidate_output/raw.json';$copy=Join-Path $input 'raw.json';if(-not(Test-Path -LiteralPath $raw -PathType Leaf)-or -not(Test-Path -LiteralPath $copy -PathType Leaf)){throw 'Auditor raw input/copy missing'};if((Get-FileHash $raw -Algorithm SHA256).Hash -ne (Get-FileHash $copy -Algorithm SHA256).Hash){throw 'Auditor input is not byte-identical'};$argsW+=@('--mount',("type=bind,source={0},target=/in,readonly" -f $input))}
$argsW+=@('--mount',("type=bind,source={0},target=/out" -f $out),'--workdir','/src',$freeze.runtime.image)+$inner
$start=[DateTime]::UtcNow.ToString('o')
& $cli @argsW 1> (Join-Path $out 'stdout.log') 2> (Join-Path $out 'stderr.log')
$code=$LASTEXITCODE
[ordered]@{stage=$Stage;cli=$cli;version=$version;image=$freeze.runtime.image;base_main=$freeze.base_main;branch=$branch;input=$input;output=$out;command=($argsW -join ' ');started_at_utc=$start;finished_at_utc=[DateTime]::UtcNow.ToString('o');exit_code=$code}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $out 'RUN.json') -Encoding utf8NoBOM
$code|Set-Content -LiteralPath (Join-Path $out 'exit.txt') -Encoding ascii
exit $code

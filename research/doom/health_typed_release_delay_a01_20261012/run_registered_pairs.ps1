$ErrorActionPreference='Stop'
$stage=Split-Path -Parent $MyInvocation.MyCommand.Path
$out=Join-Path $stage 'results'
$image='python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd'
$delay='150.031473'
$records=@()
for($pair=1;$pair -le 10;$pair++){
  if($pair % 2 -eq 1){$arms=@('early','delayed')}else{$arms=@('delayed','early')}
  foreach($arm in $arms){
    $name="pair-{0:D2}-$arm" -f $pair
    $delayValue=if($arm -eq 'early'){'0'}else{$delay}
    $log=Join-Path $out "logs\$name.log"
    & wslc.exe run --rm --pull never --name "htrel-$name" --network none --cpus 1 --memory 512m --user 65534:65534 --env "INJECT_DELAY_MS=$delayValue" --env "RESULT_NAME=$name" --mount "type=bind,source=$stage,target=/study,readonly" --mount "type=bind,source=$out,target=/out" --workdir /study $image python3 /study/run_health_release.py *> $log
    $code=$LASTEXITCODE
    $records+=@{pair=$pair;arm=$arm;delay_ms=[double]$delayValue;exit_code=$code;log=(Split-Path -Leaf $log)}
    $records | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $out 'run-status.json')
    if($code -ne 0){throw "Frozen run failed at $name with exit $code; preserved log and first result, stop without retry."}
  }
}
$records | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $out 'run-status.json')

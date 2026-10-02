$ErrorActionPreference='Stop'
function Assert-Ledger($r){
 $e=[Collections.Generic.List[string]]::new();$types=@('STAT_NULL','STAT_ALT','METHOD_PASS','STAT_NULL','STAT_INVALID_CORRELATED','STAT_ALT','METHOD_FAIL','DESCRIPTIVE','STAT_ALT','HARD_SAFETY_FAIL','STOP','STAT_NULL','STAT_ALT');$a=@($r.rows)
 if($r.allocation -ne 'PORTFOLIO-MULTIPLICITY-5890-T0-20261001-01' -or $r.base_main -ne '5865c5e74842b5bba6a6291e141afae75ca4a147' -or $r.seed -ne 58901001 -or $a.Count -ne 416){$e.Add('identity/count')}
 $o=@($a|Sort-Object {[int]$_.registered_order});$seen=@{}
 for($n=0;$n -lt $o.Count;$n++){
  $x=$o[$n];$f=[int][math]::Floor($n/13);$i=$n%13
  if($x.registered_order -ne $n+1 -or $x.id -ne ('F{0:D2}-C{1:D2}' -f $f,($i+1)) -or $x.family -ne ('F{0:D2}' -f $f) -or $x.claim_type -ne $types[$i] -or $x.portfolio_id -ne 'portfolio-5890-r1'){$e.Add("schedule-$n")}
  if($seen.ContainsKey($x.id)){$e.Add("duplicate-$n")}else{$seen[$x.id]=$true}
  if($x.completion_order -ne ($f*13+(($i*5)%13)+1)){$e.Add("completion-$n")}
  if($x.claim_type -in @('STAT_NULL','STAT_ALT')){
   if($null -eq $x.p_micro -or [int]$x.p_micro -lt 1 -or [int]$x.p_micro -gt 1000000 -or $null -eq $x.true_null -or $x.hard_safety_failure -or $x.dependence_group -ne "independent-$f-$i"){$e.Add("eligible-$n")}
   if(($x.claim_type -eq 'STAT_NULL') -ne [bool]$x.true_null){$e.Add("truth-$n")}
  }elseif($x.claim_type -eq 'STAT_INVALID_CORRELATED'){
   if($x.p_micro -ne $o[$f*13].p_micro -or $x.dependence_group -ne "shared-null-$f" -or $x.true_null -ne $true -or $x.hard_safety_failure){$e.Add("dependent-$n")}
  }elseif($x.claim_type -eq 'HARD_SAFETY_FAIL'){
   if($x.p_micro -ne 1 -or -not $x.hard_safety_failure -or $null -ne $x.true_null){$e.Add("safety-$n")}
  }else{
   if($null -ne $x.p_micro -or $null -ne $x.true_null -or $x.hard_safety_failure){$e.Add("nonnumeric-$n")}
  }
 }
 if($seen.Count -ne 416){$e.Add('unique-count')}
 if($e.Count){throw ($e -join ',')}
 return $o
}
$b64=[Console]::In.ReadLine();$cb=[Convert]::FromBase64String($b64);$mi=[IO.MemoryStream]::new($cb);$gz=[IO.Compression.GZipStream]::new($mi,[IO.Compression.CompressionMode]::Decompress);$mo=[IO.MemoryStream]::new();$gz.CopyTo($mo);$gz.Dispose();$mi.Dispose();$bytes=$mo.ToArray()
$rawText=[Text.Encoding]::UTF8.GetString($bytes);$raw=$rawText|ConvertFrom-Json;$rows=@(Assert-Ledger $raw)
$eligible=0;$nullN=0;$altN=0;$uf=0;$ut=0;$of=0;$ot=0;$bad=0
foreach($x in $rows){
 if($x.claim_type -in @('STAT_NULL','STAT_ALT')){
  $eligible++;$p=[double]$x.p_micro/1000000.0;$alpha=.05/($eligible*($eligible+1))
  if($x.true_null){$nullN++;if($p -lt .05){$uf++};if($p -lt $alpha){$of++}}
  else{$altN++;if($p -lt .05){$ut++};if($p -lt $alpha){$ot++}}
 }elseif($x.claim_type -eq 'STAT_INVALID_CORRELATED'){$bad++}
}
# Mutate independent copies; each must be rejected by the same raw-only contract.
$controls=[ordered]@{}
$m=@($rows|Where-Object{$_.claim_type -ne 'METHOD_FAIL'});try{Assert-Ledger ([pscustomobject]@{allocation=$raw.allocation;base_main=$raw.base_main;seed=$raw.seed;rows=$m})|Out-Null;$controls.omitted_failure=$false}catch{$controls.omitted_failure=$true}
$m=@($rows)+@($rows[0]);try{Assert-Ledger ([pscustomobject]@{allocation=$raw.allocation;base_main=$raw.base_main;seed=$raw.seed;rows=$m})|Out-Null;$controls.duplicate=$false}catch{$controls.duplicate=$true}
$m=@($rows|ForEach-Object{$_|ConvertTo-Json -Compress|ConvertFrom-Json});$m[0].registered_order=2;$m[1].registered_order=1;try{Assert-Ledger ([pscustomobject]@{allocation=$raw.allocation;base_main=$raw.base_main;seed=$raw.seed;rows=$m})|Out-Null;$controls.reordered_start=$false}catch{$controls.reordered_start=$true}
$m=@($rows|ForEach-Object{$_|ConvertTo-Json -Compress|ConvertFrom-Json});$m[1].dependence_group=$m[0].dependence_group;try{Assert-Ledger ([pscustomobject]@{allocation=$raw.allocation;base_main=$raw.base_main;seed=$raw.seed;rows=$m})|Out-Null;$controls.shared_cohort=$false}catch{$controls.shared_cohort=$true}
$m=@($rows|ForEach-Object{$_|ConvertTo-Json -Compress|ConvertFrom-Json});$m[0].portfolio_id='portfolio-5890-r2';try{Assert-Ledger ([pscustomobject]@{allocation=$raw.allocation;base_main=$raw.base_main;seed=$raw.seed;rows=$m})|Out-Null;$controls.posthoc_family=$false}catch{$controls.posthoc_family=$true}
$m=@($rows|ForEach-Object{$_|ConvertTo-Json -Compress|ConvertFrom-Json});$m[2].p_micro=1;try{Assert-Ledger ([pscustomobject]@{allocation=$raw.allocation;base_main=$raw.base_main;seed=$raw.seed;rows=$m})|Out-Null;$controls.invented_method_p=$false}catch{$controls.invented_method_p=$true}
$m=@($rows|ForEach-Object{$_|ConvertTo-Json -Compress|ConvertFrom-Json});$m[9].hard_safety_failure=$false;try{Assert-Ledger ([pscustomobject]@{allocation=$raw.allocation;base_main=$raw.base_main;seed=$raw.seed;rows=$m})|Out-Null;$controls.safety_forgery=$false}catch{$controls.safety_forgery=$true}
$mr=@($controls.Values|Where-Object{$_}).Count;$ufdp=if($uf+$ut){$uf/($uf+$ut)}else{0};$ofdp=if($of+$ot){$of/($of+$ot)}else{0}
$decision=if($eligible -eq 224 -and $nullN -eq 96 -and $altN -eq 128 -and $bad -eq 32 -and $of -eq 0 -and $ufdp -gt $ofdp -and $mr -eq 7){'PASS_METHOD_SCOPED'}else{'FAIL_OR_HOLD'}
[ordered]@{decision=$decision;raw_sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant();rows=$rows.Count;eligible=$eligible;null_tests=$nullN;alternative_tests=$altN;unadjusted_false=$uf;unadjusted_true=$ut;online_false=$of;online_true=$ot;unadjusted_fdp=$ufdp;online_fdp=$ofdp;invalid_correlated_refused=$bad;corruption_controls=$controls;corruptions_rejected=$mr}|ConvertTo-Json -Depth 4 -Compress

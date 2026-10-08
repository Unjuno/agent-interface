$ErrorActionPreference='Stop'
$seed=58901001;$scale=1000000;$families=32
$kinds=@('STAT_NULL','STAT_ALT','METHOD_PASS','STAT_NULL','STAT_INVALID_CORRELATED','STAT_ALT','METHOD_FAIL','DESCRIPTIVE','STAT_ALT','HARD_SAFETY_FAIL','STOP','STAT_NULL','STAT_ALT')
$rng=[Random]::new($seed);$rows=[Collections.Generic.List[object]]::new()
for($f=0;$f -lt $families;$f++){
 $first=0
 for($i=0;$i -lt 13;$i++){
  $k=$kinds[$i];$p=$null;$truth=$null;$dep=$null;$sf=$false
  switch($k){
   'STAT_NULL' {$p=$rng.Next(1,$scale+1);$truth=$true;$dep="independent-$f-$i"}
   'STAT_ALT' {$p=1+[int][math]::Floor([math]::Pow($rng.NextDouble(),5)*($scale-1));$truth=$false;$dep="independent-$f-$i"}
   'STAT_INVALID_CORRELATED' {$p=$first;$truth=$true;$dep="shared-null-$f"}
   'HARD_SAFETY_FAIL' {$p=1;$sf=$true;$dep="safety-$f"}
  }
  if($i -eq 0){$first=$p}
  $rows.Add([ordered]@{id=("F{0:D2}-C{1:D2}" -f $f,($i+1));family=("F{0:D2}" -f $f);portfolio_id='portfolio-5890-r1';registered_order=$f*13+$i+1;completion_order=$f*13+(($i*5)%13)+1;claim_type=$k;p_micro=$p;true_null=$truth;dependence_group=$dep;hard_safety_failure=$sf})
 }
}
$raw=[ordered]@{allocation='PORTFOLIO-MULTIPLICITY-5890-T0-20261001-01';base_main='5865c5e74842b5bba6a6291e141afae75ca4a147';seed=$seed;rows=$rows}
$json=ConvertTo-Json -InputObject $raw -Depth 5 -Compress;$bytes=[Text.Encoding]::UTF8.GetBytes($json)
$sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
$ms=[IO.MemoryStream]::new();$gz=[IO.Compression.GZipStream]::new($ms,[IO.Compression.CompressionLevel]::Optimal,$true);$gz.Write($bytes,0,$bytes.Length);$gz.Dispose()
$out=[ordered]@{raw_sha256=$sha;gzip_sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray())).ToLowerInvariant();raw_bytes=$bytes.Length;gzip_base64=[Convert]::ToBase64String($ms.ToArray())}
$ms.Dispose();$out|ConvertTo-Json -Compress

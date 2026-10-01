param(
  [switch]$PreflightOnly,
  [switch]$RunConstruction
)
$ErrorActionPreference = 'Stop'
if ($PreflightOnly -eq $RunConstruction) { throw 'Specify exactly one of -PreflightOnly or -RunConstruction.' }
$Source = Split-Path -Parent $PSCommandPath
$RepoRoot = 'C:\Users\junny\Documents\Codex\2026-09-19\new-chat'
$Out = Join-Path $RepoRoot 'work\issue4912-v5-construction-out-20260928'
$Logs = Join-Path $RepoRoot 'work\issue4912-v5-host-logs-20260928'
$Model = 'C:\Users\junny\.cache\huggingface\hub\models--Qwen--Qwen2.5-0.5B-Instruct\snapshots\7ae557604adf67be50417f59c2c2f167def9a775'
$Image = 'sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261'
$Allocation = 'typed-readout-precision-boundary-1014-v5-20260928-01'
$ExpectedCorpus = '85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c'
$ExpectedWeights = 'fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe'
$Manifest = Get-Content -LiteralPath (Join-Path $Source 'SOURCE_MANIFEST.json') -Raw | ConvertFrom-Json
if ($Manifest.allocation -ne $Allocation) { throw 'STOP_ALLOCATION_MANIFEST_MISMATCH' }
foreach ($file in $Manifest.files) {
  $path = Join-Path $Source $file.path
  if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "STOP_SOURCE_MISSING:$($file.path)" }
  if ((Get-Item -LiteralPath $path).Length -ne $file.bytes) { throw "STOP_SOURCE_SIZE_MISMATCH:$($file.path)" }
  if ((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower() -ne $file.sha256) { throw "STOP_SOURCE_HASH_MISMATCH:$($file.path)" }
}
if ((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Source 'corpus.jsonl')).Hash.ToLower() -ne $ExpectedCorpus) { throw 'STOP_CORPUS_HASH_MISMATCH' }
$modelManifest = Get-Content -LiteralPath (Join-Path $Source 'MODEL_MANIFEST.json') -Raw | ConvertFrom-Json
foreach ($file in $modelManifest.files) {
  $path = Join-Path $Model $file.path
  if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "STOP_MODEL_ASSET_MISSING:$($file.path)" }
  if ((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower() -ne $file.sha256) { throw "STOP_MODEL_ASSET_HASH_MISMATCH:$($file.path)" }
}
if ((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Model 'model.safetensors')).Hash.ToLower() -ne $ExpectedWeights) { throw 'STOP_WEIGHT_HASH_MISMATCH' }
if (!(Test-Path -LiteralPath $Out -PathType Container) -or (Get-ChildItem -LiteralPath $Out -Force | Measure-Object).Count -ne 0) { throw 'STOP_OUTPUT_NOT_EMPTY' }
if (!(Test-Path -LiteralPath $Logs -PathType Container)) { throw 'STOP_LOG_DIRECTORY_MISSING' }
$existingMarker = Join-Path $Logs 'construction_invocation_started.lock'
if (Test-Path -LiteralPath $existingMarker) { throw 'STOP_ALLOCATION_ALREADY_INVOKED_NO_RETRY' }
$imageId = docker image inspect $Image --format '{{.Id}}'
if ($LASTEXITCODE -ne 0 -or $imageId -ne $Image) { throw 'STOP_IMAGE_ID_MISMATCH' }
if ($RunConstruction) {
  $gpuLine = (nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits | Select-Object -First 1).Trim()
  if ($LASTEXITCODE -ne 0 -or $gpuLine -ne '0, 0') { throw "STOP_GPU_NOT_IDLE:$gpuLine" }
}
$dockerArgv = @('--rm','--pull=never','--network','none','--read-only','--gpus','all','--cpus=2','--memory=8g','--pids-limit=64','--tmpfs','/tmp:rw,noexec,nosuid,size=512m','--mount',"type=bind,source=$Source,target=/src,readonly",'--mount',"type=bind,source=$Model,target=/models/model,readonly",'--mount',"type=bind,source=$Out,target=/out",'--env','HF_HOME=/tmp/hf','--env','TRANSFORMERS_OFFLINE=1','--entrypoint','python',$Image,'-B','/src/run_construction.py','--model','/models/model','--corpus','/src/corpus.jsonl','--out','/out')
$command = 'docker run ' + ($dockerArgv -join ' ')
if ($PreflightOnly) { [pscustomobject]@{ status='PREFLIGHT_PASS'; allocation=$Allocation; image_id=$imageId; corpus_sha256=$ExpectedCorpus; output_empty=$true; one_shot_marker_exists=$false; docker_command=$command } | ConvertTo-Json -Compress; exit 0 }
New-Item -ItemType File -Path $existingMarker | Out-Null
[IO.File]::WriteAllText($existingMarker,($command + "`n" + (Get-Date).ToUniversalTime().ToString('o')),[Text.UTF8Encoding]::new($false))
$stdout = Join-Path $Logs 'construction.stdout.log'
$stderr = Join-Path $Logs 'construction.stderr.log'
$started = (Get-Date).ToUniversalTime().ToString('o')
& docker run @dockerArgv 1> $stdout 2> $stderr
$dockerExit = $LASTEXITCODE
$receipt = [ordered]@{ allocation=$Allocation; command=$command; exit_code=$dockerExit; started_utc=$started; ended_utc=(Get-Date).ToUniversalTime().ToString('o'); stdout_bytes=(Get-Item -LiteralPath $stdout).Length; stderr_bytes=(Get-Item -LiteralPath $stderr).Length; corpus_sha256=$ExpectedCorpus; image_id=$imageId; retry=0 }
[IO.File]::WriteAllText((Join-Path $Logs 'invocation.json'),($receipt | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
exit $dockerExit

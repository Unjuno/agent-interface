param([switch]$PreflightOnly)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$freeze = Get-Content -LiteralPath (Join-Path $root 'FREEZE.json') -Raw | ConvertFrom-Json
$modelRoot = 'C:\Users\junny\.cache\huggingface\hub\models--autogluon--mitra-classifier-2\snapshots\edada0d20759c58ada8c8605c25f22f6e98ea5f0'
$modelPath = Join-Path $modelRoot 'model.safetensors'
$formalOut = Join-Path $root 'formal-01'
$auditOut = Join-Path $root 'audit-01'
$hostEvidence = Join-Path $root 'host-evidence-01'
$image = $freeze.execution.image_id

function Assert-Hash($Path, $Expected) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { throw "MISSING_FILE:$Path" }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLower()
    if ($actual -ne $Expected.ToLower()) { throw "SHA256_MISMATCH:${Path}:$actual" }
}

foreach ($entry in $freeze.source_sha256.PSObject.Properties) {
    Assert-Hash (Join-Path $root $entry.Name) $entry.Value
}
Assert-Hash (Join-Path $root 'inputs\support.csv') $freeze.inputs.support.sha256
Assert-Hash (Join-Path $root 'inputs\queries.csv') $freeze.inputs.queries.sha256
Assert-Hash $modelPath $freeze.model.sha256
$imageId = docker image inspect $image --format '{{.Id}} {{.Os}}/{{.Architecture}}'
if ($LASTEXITCODE -ne 0 -or $imageId -notmatch [regex]::Escape($image)) { throw 'PINNED_IMAGE_MISSING_OR_MISMATCH' }
$gpu = nvidia-smi --query-gpu=name,memory.used --format=csv,noheader
if ($LASTEXITCODE -ne 0 -or $gpu -notmatch 'RTX 3080' -or $gpu -notmatch '0 MiB') { throw "GPU_NOT_IDLE_OR_UNEXPECTED:$gpu" }
$running = @(docker ps --no-trunc --format '{{.ID}}|{{.Names}}|{{.Image}}') | Sort-Object
$expectedRunning = @($freeze.execution.container_allowlist) | Sort-Object
if (($running -join "`n") -ne ($expectedRunning -join "`n")) { throw 'RUNNING_CONTAINER_SET_CHANGED; inspect all containers and active allocations' }
if (Test-Path -LiteralPath $formalOut) { throw 'FORMAL_OUTPUT_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $auditOut) { throw 'AUDIT_OUTPUT_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $hostEvidence) { throw 'HOST_EVIDENCE_ALREADY_EXISTS' }
$preflight = [ordered]@{ schema='mitra-mode-preflight-4935-v1'; issue=4935; allocation=$freeze.allocation; utc=[DateTime]::UtcNow.ToString('o'); main_sha=$freeze.main_intake_sha; image_id=$imageId.Trim(); gpu=$gpu.Trim(); running_containers=(docker ps --no-trunc --format '{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}'); model_sha256=(Get-FileHash -Algorithm SHA256 $modelPath).Hash.ToLower(); input_hashes=@{support=(Get-FileHash -Algorithm SHA256 (Join-Path $root 'inputs\support.csv')).Hash.ToLower();queries=(Get-FileHash -Algorithm SHA256 (Join-Path $root 'inputs\queries.csv')).Hash.ToLower()} }
if ($PreflightOnly) { $preflight | ConvertTo-Json -Depth 8; exit 0 }

# The preflight must be reviewed against current Codex allocations immediately before launch.
New-Item -ItemType Directory -Path $formalOut | Out-Null
New-Item -ItemType Directory -Path $auditOut | Out-Null
New-Item -ItemType Directory -Path $hostEvidence | Out-Null
$srcMount = "type=bind,source=$root,target=/src,readonly"
$inputMount = "type=bind,source=$(Join-Path $root 'inputs'),target=/inputs,readonly"
$modelMount = "type=bind,source=$modelRoot,target=/model,readonly"
$outMount = "type=bind,source=$formalOut,target=/out"
$runnerArgs = @('run','--rm','--pull=never','--gpus','all','--network','none','--read-only','--cpus=1','--memory=4g','--pids-limit=128','--mount',$srcMount,'--mount',$inputMount,'--mount',$modelMount,'--mount',$outMount,'--entrypoint','python',$image,'/src/probe.py')
$runStarted = [DateTime]::UtcNow.ToString('o')
& docker @runnerArgs 1> (Join-Path $hostEvidence 'runner.stdout.txt') 2> (Join-Path $hostEvidence 'runner.stderr.txt')
$runnerExit = $LASTEXITCODE
$runnerReceipt = [ordered]@{schema='mitra-mode-invocation-4935-v1';issue=4935;allocation=$freeze.allocation;started_utc=$runStarted;finished_utc=[DateTime]::UtcNow.ToString('o');command=(@('docker')+$runnerArgs);exit_code=$runnerExit;image_id=$imageId.Trim();gpu=$gpu.Trim();prelaunch_containers=$running}
$runnerReceipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $hostEvidence 'INVOCATION.json') -Encoding utf8NoBOM
if ($runnerExit -ne 0 -or !(Test-Path -LiteralPath (Join-Path $formalOut 'RAW.json'))) { throw 'FORMAL_RUNNER_STOP; preserve raw output and do not retry' }
$rawMount = "type=bind,source=$(Join-Path $formalOut 'RAW.json'),target=/raw/RAW.json,readonly"
$auditSrc = "type=bind,source=$root,target=/src,readonly"
$auditMount = "type=bind,source=$auditOut,target=/out"
$auditArgs = @('run','--rm','--pull=never','--network','none','--read-only','--cpus=1','--memory=1g','--pids-limit=64','--mount',$auditSrc,'--mount',$rawMount,'--mount',$auditMount,'--entrypoint','python',$image,'/src/audit.py','/raw/RAW.json','/out/AUDIT.json')
& docker @auditArgs 1> (Join-Path $hostEvidence 'auditor.stdout.txt') 2> (Join-Path $hostEvidence 'auditor.stderr.txt')
if ($LASTEXITCODE -ne 0) { throw 'AUDITOR_FAILED; preserve all outputs and do not retry' }
$preflight | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $auditOut 'PREFLIGHT.json') -Encoding utf8NoBOM
$rawHash = (Get-FileHash -Algorithm SHA256 (Join-Path $formalOut 'RAW.json')).Hash.ToLower()
$auditHash = (Get-FileHash -Algorithm SHA256 (Join-Path $auditOut 'AUDIT.json')).Hash.ToLower()
[ordered]@{schema='mitra-mode-output-manifest-4935-v1';raw_sha256=$rawHash;audit_sha256=$auditHash;invocation_sha256=(Get-FileHash -Algorithm SHA256 (Join-Path $hostEvidence 'INVOCATION.json')).Hash.ToLower()} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $hostEvidence 'OUTPUT_MANIFEST.json') -Encoding utf8NoBOM

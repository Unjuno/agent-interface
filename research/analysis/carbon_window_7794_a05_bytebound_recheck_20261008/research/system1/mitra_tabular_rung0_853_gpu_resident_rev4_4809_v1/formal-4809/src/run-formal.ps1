param(
    [Parameter(Mandatory = $true)]
    [string]$CollisionEvidencePath
)
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path $PSScriptRoot).Path
$modelPath = 'C:\Users\junny\.cache\huggingface\hub\models--autogluon--mitra-classifier-2\snapshots\edada0d20759c58ada8c8605c25f22f6e98ea5f0'
$image = 'mitra-rung0-853-rev4:local-20260927'
$runnerName = 'mitra4809-formal-run-01'
$auditName = 'mitra4809-formal-audit-01'
$stopAuditName = 'mitra4809-formal-stop-audit-01'
$outPath = Join-Path (Split-Path $repoRoot) 'formal-01'
$inputPath = Join-Path (Split-Path $repoRoot) 'inputs'

if (!(Test-Path -LiteralPath $CollisionEvidencePath)) { throw 'Collision evidence is missing; formal invocation not started.' }
$collision = Get-Content -LiteralPath $CollisionEvidencePath -Raw | ConvertFrom-Json
if ($collision.schema -ne 'shared-rtx3080-collision-clear-v1' -or $collision.issue -ne 4809 -or $collision.clear -ne $true) {
    throw 'Collision evidence does not clear Issue #4809; formal invocation not started.'
}
if (@($collision.active_gpu_allocations).Count -ne 0 -or @($collision.active_codex_gpu_tasks).Count -ne 0) {
    throw 'An overlapping GPU allocation or Codex task remains active; formal invocation not started.'
}
$checkedAt = [DateTimeOffset]::Parse($collision.checked_at_utc)
$age = [DateTimeOffset]::UtcNow - $checkedAt.ToUniversalTime()
if ($age.TotalSeconds -lt -30 -or $age.TotalMinutes -gt 3) { throw 'Collision evidence is not fresh (must be checked within the last 3 minutes).' }

$freezePath = Join-Path $repoRoot 'FREEZE.json'
$freeze = Get-Content -LiteralPath $freezePath -Raw | ConvertFrom-Json
foreach ($relative in $freeze.source_sha256.PSObject.Properties.Name) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $repoRoot $relative) -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $freeze.source_sha256.$relative) { throw "Frozen source mismatch: $relative" }
}
foreach ($pair in @(
    @('support.csv', $freeze.inputs.support.sha256),
    @('queries.csv', $freeze.inputs.queries.sha256)
)) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $inputPath $pair[0]) -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $pair[1]) { throw "Frozen input mismatch: $($pair[0])" }
}
foreach ($pair in @(
    @('model.safetensors', $freeze.inputs.model.sha256),
    @('config.json', $freeze.inputs.config.sha256),
    @('README.md', $freeze.inputs.model_card.sha256)
)) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $modelPath $pair[0]) -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $pair[1]) { throw "Frozen model artifact mismatch: $($pair[0])" }
}

$imageId = docker image inspect $image --format '{{.Id}}'
if ($LASTEXITCODE -ne 0 -or $imageId -ne $freeze.runtime.formal_image_id) { throw 'Formal image ID mismatch; invocation not started.' }
$gpu = @(nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader)
if ($LASTEXITCODE -ne 0 -or $gpu.Count -ne 1 -or $gpu[0] -notmatch 'RTX 3080 Laptop GPU,\s*16384 MiB,\s*0 MiB,\s*0 %') {
    throw 'Local RTX 3080 is not idle/available; formal invocation not started.'
}
$running = @(docker ps --format '{{.Names}}')
$allowedContainers = @($collision.allowed_running_containers)
$allowed = @($allowedContainers | ForEach-Object { $_.name })
$runningKey = (($running | Sort-Object) -join ',')
$allowedKey = (($allowed | Sort-Object) -join ',')
if ($runningKey -ne $allowedKey) {
    throw "Running Docker containers differ from the reviewed collision evidence: $($running -join ',')"
}
foreach ($expectedContainer in $allowedContainers) {
    $actualContainer = docker inspect $expectedContainer.name | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or $actualContainer[0].Id -ne $expectedContainer.id -or $actualContainer[0].Config.Image -ne $expectedContainer.image -or $actualContainer[0].State.Status -ne 'running') {
        throw "Allowed running container changed since collision audit: $($expectedContainer.name)"
    }
}
if ((docker ps -a --format '{{.Names}}') -contains $runnerName -or (docker ps -a --format '{{.Names}}') -contains $auditName -or (docker ps -a --format '{{.Names}}') -contains $stopAuditName) {
    throw 'A one-shot container name already exists; refusing duplicate allocation.'
}
if (Test-Path -LiteralPath $outPath) { throw 'Formal output path already exists; refusing overwrite or retry.' }

New-Item -ItemType Directory -Path $outPath | Out-Null
Copy-Item -LiteralPath $CollisionEvidencePath -Destination (Join-Path $outPath 'COLLISION_EVIDENCE.json')
$gpu | Set-Content -LiteralPath (Join-Path $outPath 'GPU_PRE.csv') -Encoding utf8
$started = [ordered]@{
    schema = 'issue-4809-formal-invocation-start-v1'
    allocation = $freeze.allocation
    issue = 4809
    freeze_sha256 = (Get-FileHash -LiteralPath $freezePath -Algorithm SHA256).Hash.ToLower()
    collision_evidence_sha256 = (Get-FileHash -LiteralPath $CollisionEvidencePath -Algorithm SHA256).Hash.ToLower()
    image_id = $imageId
    started_at_utc = [DateTime]::UtcNow.ToString('o')
}
$started | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $outPath 'INVOCATION_STARTED.json') -Encoding utf8

$sourceMount = "type=bind,source=$repoRoot,target=/src,readonly"
$inputMount = "type=bind,source=$inputPath,target=/inputs,readonly"
$modelMount = "type=bind,source=$modelPath,target=/model,readonly"
$outputMount = "type=bind,source=$outPath,target=/out"
$runnerArgs = @(
    'run', '--name', $runnerName, '--pull=never', '--gpus', 'all', '--network', 'none', '--read-only',
    '--cpus=1', '--memory=4g', '--pids-limit=128', '--tmpfs', '/tmp:rw,nosuid,nodev,size=512m',
    '--mount', $sourceMount, '--mount', $inputMount, '--mount', $modelMount, '--mount', $outputMount, $image
)
$runnerLog = Join-Path $outPath 'runner.log'
& docker @runnerArgs *> $runnerLog
$runnerExit = $LASTEXITCODE
$gpuPost = @(nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader)
$gpuPost | Set-Content -LiteralPath (Join-Path $outPath 'GPU_POST.csv') -Encoding utf8
$runnerInspect = docker inspect $runnerName | ConvertFrom-Json
$runnerInspect | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath (Join-Path $outPath 'runner-container-inspect.json') -Encoding utf8

$auditNameUsed = $null
$auditExit = -2
$auditLogSha = $null
if (Test-Path -LiteralPath (Join-Path $outPath 'RESULT.json')) {
    $auditNameUsed = $auditName
    $auditArgs = @(
        'run', '--name', $auditName, '--pull=never', '--network', 'none', '--read-only', '--cpus=1', '--memory=1g', '--pids-limit=64',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=256m', '--mount', $sourceMount, '--mount', $inputMount, '--mount', $modelMount, '--mount', $outputMount,
        '--entrypoint', 'python', $image, '/src/audit.py'
    )
    & docker @auditArgs *> (Join-Path $outPath 'audit.log')
    $auditExit = $LASTEXITCODE
    docker inspect $auditName | ConvertFrom-Json | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath (Join-Path $outPath 'audit-container-inspect.json') -Encoding utf8
    $auditLogSha = (Get-FileHash -LiteralPath (Join-Path $outPath 'audit.log') -Algorithm SHA256).Hash.ToLower()
} elseif (Test-Path -LiteralPath (Join-Path $outPath 'STOP.json')) {
    $auditNameUsed = $stopAuditName
    $stopArgs = @(
        'run', '--name', $stopAuditName, '--pull=never', '--network', 'none', '--read-only', '--cpus=1', '--memory=512m', '--pids-limit=64',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m', '--mount', $sourceMount, '--mount', $outputMount,
        '--entrypoint', 'python', $image, '/src/stop_audit.py'
    )
    & docker @stopArgs *> (Join-Path $outPath 'stop-audit.log')
    $auditExit = $LASTEXITCODE
    docker inspect $stopAuditName | ConvertFrom-Json | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath (Join-Path $outPath 'stop-audit-container-inspect.json') -Encoding utf8
    $auditLogSha = (Get-FileHash -LiteralPath (Join-Path $outPath 'stop-audit.log') -Algorithm SHA256).Hash.ToLower()
}

$invocation = [ordered]@{
    schema = 'issue-4809-formal-invocation-v1'
    allocation = $freeze.allocation
    freeze_sha256 = (Get-FileHash -LiteralPath $freezePath -Algorithm SHA256).Hash.ToLower()
    collision_evidence_sha256 = $started.collision_evidence_sha256
    image_id = $imageId
    runner_container = $runnerName
    runner_exit_code = $runnerExit
    runner_state = $runnerInspect[0].State
    runner_network_mode = $runnerInspect[0].HostConfig.NetworkMode
    runner_readonly_rootfs = $runnerInspect[0].HostConfig.ReadonlyRootfs
    runner_memory_bytes = $runnerInspect[0].HostConfig.Memory
    runner_pids_limit = $runnerInspect[0].HostConfig.PidsLimit
    runner_log_sha256 = (Get-FileHash -LiteralPath $runnerLog -Algorithm SHA256).Hash.ToLower()
    gpu_pre = $gpu
    gpu_post = $gpuPost
    audit_container = $auditNameUsed
    audit_exit_code = $auditExit
    audit_log_sha256 = $auditLogSha
    network_during_formal = 'none'
    formal_gpu_requested = $true
}
$invocation | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath (Join-Path $outPath 'FORMAL_INVOCATION.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $outPath 'FORMAL_INVOCATION.json') -Raw
if ($runnerExit -ne 0 -or $auditExit -ne 0) { exit 1 }

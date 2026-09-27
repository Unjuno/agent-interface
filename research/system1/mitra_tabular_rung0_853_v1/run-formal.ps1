$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path $PSScriptRoot).Path
$modelPath = 'C:\Users\junny\.cache\huggingface\hub\models--autogluon--mitra-classifier-2\snapshots\edada0d20759c58ada8c8605c25f22f6e98ea5f0'
$outPath = Join-Path $repoRoot 'formal-01'
$image = 'mitra-rung0-853:local-20260927'
$runnerName = 'mitra-rung0-853-formal-01'
$auditName = 'mitra-rung0-853-audit-01'

if (!(Test-Path -LiteralPath (Join-Path $modelPath 'model.safetensors'))) {
    throw 'Pinned local model file is missing; formal allocation not started.'
}
if (!(Test-Path -LiteralPath (Join-Path $repoRoot 'FREEZE.json'))) {
    throw 'FREEZE.json is missing; formal allocation not started.'
}
if (docker ps -a --format '{{.Names}}' | Where-Object { $_ -in @($runnerName, $auditName) }) {
    throw 'A frozen allocation container name already exists; refusing duplicate invocation.'
}
if (!(Test-Path -LiteralPath $outPath)) {
    New-Item -ItemType Directory -Path $outPath | Out-Null
}

$freeze = Get-Content -LiteralPath (Join-Path $repoRoot 'FREEZE.json') -Raw | ConvertFrom-Json
$localImageId = docker image inspect $image --format '{{.Id}}'
if ($LASTEXITCODE -ne 0 -or $localImageId -ne $freeze.runtime.measured_image_id) {
    throw 'Local Docker image does not match the frozen image ID; allocation not started.'
}
$sourceMount = "type=bind,source=$repoRoot,target=/src,readonly"
$modelMount = "type=bind,source=$modelPath,target=/model,readonly"
$outputMount = "type=bind,source=$outPath,target=/out"
$preGpu = Join-Path $outPath 'GPU_PRE.csv'
$postGpu = Join-Path $outPath 'GPU_POST.csv'
$runnerLog = Join-Path $outPath 'runner.log'
$auditLog = Join-Path $outPath 'audit.log'

nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader | Set-Content -LiteralPath $preGpu -Encoding utf8
$timer = [System.Diagnostics.Stopwatch]::StartNew()
$runnerArgs = @(
    'run', '--name', $runnerName, '--network', 'none', '--read-only',
    '--cpus=1', '--memory=4g', '--pids-limit=128',
    '--tmpfs', '/tmp:rw,nosuid,nodev,size=512m',
    '--mount', $sourceMount, '--mount', $modelMount, '--mount', $outputMount,
    $image
)
& docker @runnerArgs *> $runnerLog
$runnerExit = $LASTEXITCODE
$timer.Stop()
nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader | Set-Content -LiteralPath $postGpu -Encoding utf8
$runnerInspect = docker inspect $runnerName | ConvertFrom-Json
$runnerInspect | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath (Join-Path $outPath 'runner-container-inspect.json') -Encoding utf8

$auditExit = -2
$auditArgs = @()
$auditorContainer = $null
$auditorLogSha = $null
if (Test-Path -LiteralPath (Join-Path $outPath 'RESULT.json')) {
    $auditArgs = @(
        'run', '--name', $auditName, '--network', 'none', '--read-only',
        '--cpus=1', '--memory=1g', '--pids-limit=64',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=256m',
        '--mount', $sourceMount, '--mount', $modelMount, '--mount', $outputMount,
        '--entrypoint', 'python', $image, '/src/audit.py'
    )
    & docker @auditArgs *> $auditLog
    $auditExit = $LASTEXITCODE
    $auditorContainer = $auditName
    $auditInspect = docker inspect $auditName | ConvertFrom-Json
    $auditInspect | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath (Join-Path $outPath 'audit-container-inspect.json') -Encoding utf8
    if (Test-Path -LiteralPath $auditLog) {
        $auditorLogSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $auditLog).Hash.ToLower()
    }
}

$invocation = [ordered]@{
    schema = 'issue-853-mitra-rung0-invocation-v1'
    allocation = $freeze.allocation
    freeze_file_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repoRoot 'FREEZE.json')).Hash.ToLower()
    image = $image
    image_id = $localImageId
    runner_docker_args = $runnerArgs
    runner_container = $runnerName
    runner_exit_code = $runnerExit
    runner_state = $runnerInspect[0].State
    runner_network_mode = $runnerInspect[0].HostConfig.NetworkMode
    runner_readonly_rootfs = $runnerInspect[0].HostConfig.ReadonlyRootfs
    runner_memory_bytes = $runnerInspect[0].HostConfig.Memory
    runner_pids_limit = $runnerInspect[0].HostConfig.PidsLimit
    host_wall_seconds = $timer.Elapsed.TotalSeconds
    runner_log_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $runnerLog).Hash.ToLower()
    gpu_pre_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $preGpu).Hash.ToLower()
    gpu_post_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $postGpu).Hash.ToLower()
    auditor_container = $auditorContainer
    auditor_docker_args = $auditArgs
    auditor_exit_code = $auditExit
    auditor_log_sha256 = $auditorLogSha
    network_during_measured_run = 'none'
    gpu_used_for_measurement = $false
}
$invocation | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $outPath 'FORMAL_INVOCATION.json') -Encoding utf8

Get-Content -LiteralPath (Join-Path $outPath 'FORMAL_INVOCATION.json') -Raw
if ($runnerExit -ne 0) { exit $runnerExit }
if ($auditExit -ne 0) { exit 1 }

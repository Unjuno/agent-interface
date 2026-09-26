param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('formal', 'audit')]
    [string]$Mode
)

$ErrorActionPreference = 'Stop'
$study = (Resolve-Path $PSScriptRoot).Path
$repo = (Resolve-Path (Join-Path $study '../../..')).Path
$runtime = (Resolve-Path (Join-Path $repo 'runtime')).Path
$freeze = Get-Content (Join-Path $study 'FREEZE.json') -Raw | ConvertFrom-Json
$formal = Join-Path $study $freeze.formal_result_path

foreach ($entry in $freeze.sha256.PSObject.Properties) {
    $relative = $entry.Name -replace '^study/', ''
    $path = if ($entry.Name.StartsWith('study/')) { Join-Path $study $relative } else { Join-Path $repo $entry.Name }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Frozen file missing: $($entry.Name)" }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $entry.Value) { throw "Frozen SHA-256 mismatch: $($entry.Name) expected=$($entry.Value) actual=$actual" }
}
foreach ($entry in $freeze.source_git_blobs.PSObject.Properties) {
    $path = Join-Path $repo $entry.Name
    $actual = (& git -C $repo hash-object --no-filters -- $path).Trim()
    if ($actual -ne $entry.Value) { throw "Frozen Git blob mismatch: $($entry.Name) expected=$($entry.Value) actual=$actual" }
}

$context = (& docker context show).Trim()
$engineParts = ((& docker info --format '{{.ServerVersion}}|{{.OSType}}|{{.Architecture}}').Trim() -split '\|')
$imageParts = ((& docker image inspect python:3.12-slim --format '{{.Id}}|{{.Os}}|{{.Architecture}}').Trim() -split '\|')
if ($context -ne 'desktop-linux' -or $engineParts.Count -ne 3 -or
    $engineParts[0] -ne $freeze.engine.version -or $engineParts[1] -ne 'linux' -or
    $engineParts[2] -ne 'x86_64' -or $imageParts.Count -ne 3 -or
    $imageParts[0] -ne $freeze.image.id -or $imageParts[1] -ne 'linux' -or
    $imageParts[2] -ne 'amd64') {
    throw "Frozen Docker preflight mismatch: context=$context engine=$($engineParts -join '|') image=$($imageParts -join '|')"
}

if ($Mode -eq 'formal') {
    $branch = (& git -C $repo branch --show-current).Trim()
    $head = (& git -C $repo rev-parse HEAD).Trim()
    $mainHead = (& git -C $repo rev-parse origin/main).Trim()
    $freezeDate = (& git -C $repo show -s --format=%cI $head).Trim()
    $remoteBranchLine = (& git -C $repo ls-remote --heads origin "refs/heads/$($freeze.branch)").Trim()
    $workingChanges = (& git -C $repo status --porcelain=v1 --untracked-files=all) -join "`n"
    if ($branch -ne $freeze.branch -or $mainHead -ne $freeze.base_main_commit -or
        $remoteBranchLine -notmatch "^$head\s+refs/heads/$([regex]::Escape($freeze.branch))$" -or $workingChanges) {
        throw "Git preflight mismatch: branch=$branch head=$head origin_main=$mainHead changes=$workingChanges remote=$remoteBranchLine"
    }
    if (Test-Path $formal) { throw "Formal output already exists; refusing a second invocation: $formal" }
    $containerName = 'agent-interface-3926-formal02-20260926'
    $evidence = Join-Path $formal 'raw'
    $output = $formal
    $entry = @('/study/test_contract.py')
    $evidenceMode = $null
    $containerCommand = 'test_contract.py'
} else {
    if (-not (Test-Path (Join-Path $formal 'formal_run.json'))) { throw 'Formal run metadata missing; cannot audit' }
    $containerName = 'agent-interface-3926-audit02-20260926'
    $evidence = Join-Path $formal 'raw'
    $output = Join-Path $formal 'audit'
    $entry = @('/study/audit_contract.py', '--evidence', '/evidence', '--output', '/audit-out/audit.json',
               '--study', '/study', '--workspace', '/source')
    $evidenceMode = 'readonly'
    $containerCommand = 'audit_contract.py'
}
if ($Mode -eq 'audit' -and (Test-Path $output)) { throw "Audit output already exists; refusing a second audit invocation: $output" }

$existing = & docker container ls -a --filter "name=^/$containerName$" --format '{{.Names}}'
if ($existing) { throw "Container name already exists; refusing reuse: $containerName" }
$evidenceMount = "type=bind,source=$evidence,target=/evidence"
if ($evidenceMode) { $evidenceMount += ",$evidenceMode" }
$imageArgs = @('run', '--name', $containerName, '--pull=never', '--platform', 'linux/amd64',
    '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
    '--pids-limit', '64', '--memory', '268435456', '--cpus', '1',
    '--tmpfs', '/tmp:rw,exec,nosuid,nodev,size=32m',
    '--mount', "type=bind,source=$study,target=/study,readonly",
    '--mount', "type=bind,source=$runtime,target=/source/runtime,readonly",
    '--mount', $evidenceMount)
if ($Mode -eq 'formal') {
    $null = New-Item -ItemType Directory -Path $evidence -Force
} else {
    $null = New-Item -ItemType Directory -Path $output -Force
    $imageArgs += @('--mount', "type=bind,source=$output,target=/audit-out")
}
$imageArgs += @('--env', 'BROKER_REPO_ROOT=/source', '--env',
    'BROKER_SOURCE_PATH=/source/runtime/host_model_ipc_broker_v1.py', '--env', 'EVIDENCE_DIR=/evidence',
    '--entrypoint', 'python', 'python:3.12-slim')
$imageArgs += $entry

$commandRecord = [ordered]@{
    mode = $Mode
    command = @('docker') + $imageArgs
    context = $context
    engine = [ordered]@{ version = $engineParts[0]; os = $engineParts[1]; architecture = $engineParts[2] }
    image = [ordered]@{ id = $imageParts[0]; os = $imageParts[1]; architecture = $imageParts[2] }
    container_name = $containerName
    container_command = $containerCommand
}
if ($Mode -eq 'formal') {
    $commandRecord.branch = $branch
    $commandRecord.freeze_commit = $head
    $commandRecord.freeze_commit_date = $freezeDate
    $commandRecord.base_main_commit = $mainHead
}
$transcriptPath = Join-Path $output ("$Mode-docker-stdout.txt")
$inspectPath = Join-Path $output ("$Mode-container-inspect.json")
$statusPath = Join-Path $output ("$Mode-run.json")

$console = & docker @imageArgs 2>&1
$dockerExit = $LASTEXITCODE
[IO.File]::WriteAllText($transcriptPath, (($console | ForEach-Object { [string]$_ }) -join "`n") + "`n", [Text.UTF8Encoding]::new($false))
$inspect = $null
$inspectExit = 127
$stateExit = $null
$containerImageId = $null
$removeExit = $null
$inspection = & docker inspect $containerName 2>&1
$inspectExit = $LASTEXITCODE
if ($inspectExit -eq 0) {
    $inspectRaw = ($inspection | ForEach-Object { [string]$_ }) -join "`n"
    [IO.File]::WriteAllText($inspectPath, $inspectRaw + "`n", [Text.UTF8Encoding]::new($false))
    $inspect = $inspectRaw | ConvertFrom-Json
    if ($inspect -is [array]) { $inspect = $inspect[0] }
    $stateExit = $inspect.State.ExitCode
    $containerImageId = $inspect.Image
    & docker rm $containerName | Out-Null
    $removeExit = $LASTEXITCODE
} else {
    [IO.File]::WriteAllText($inspectPath, (($inspection | ForEach-Object { [string]$_ }) -join "`n") + "`n", [Text.UTF8Encoding]::new($false))
}
$commandRecord.docker_exit_code = $dockerExit
$commandRecord.inspect_exit_code = $inspectExit
$commandRecord.container_exit_code = $stateExit
$commandRecord.container_image_id = $containerImageId
$commandRecord.removed_after_capture = $removeExit -eq 0
$commandRecord.remove_exit_code = $removeExit
$commandRecord.transcript_file = (Split-Path $transcriptPath -Leaf)
[IO.File]::WriteAllText($statusPath, ($commandRecord | ConvertTo-Json -Depth 12) + "`n", [Text.UTF8Encoding]::new($false))
Get-Content $statusPath
if ($dockerExit -ne 0) { exit $dockerExit }
if ($inspectExit -ne 0 -or $stateExit -ne 0 -or $containerImageId -ne $imageParts[0]) { exit 1 }

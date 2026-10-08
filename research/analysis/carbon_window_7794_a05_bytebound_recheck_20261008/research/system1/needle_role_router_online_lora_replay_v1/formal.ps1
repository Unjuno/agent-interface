param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$Allocation = 'needle-role-router-online-lora-replay-20260927-v1'
$ImageId = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$SeedList = '736211,736311,736411'
$Source = (Resolve-Path -LiteralPath $SourcePath).Path
$FreezePath = Join-Path $Source 'FREEZE.json'
$FreezeBytes = [IO.File]::ReadAllBytes($FreezePath)
$FreezeSha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($FreezeBytes)).ToLowerInvariant()
$Freeze = [Text.Encoding]::UTF8.GetString($FreezeBytes) | ConvertFrom-Json
$Sidecar = [IO.File]::ReadAllBytes((Join-Path $Source 'FREEZE.sha256'))
    if ([Text.Encoding]::ASCII.GetString($Sidecar) -cne "$FreezeSha`n") { throw 'STOP_FREEZE_SIDECAR_NOT_BARE_HEX' }
foreach ($Entry in $Freeze.source_sha256.PSObject.Properties) {
    $Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Source $Entry.Name)).Hash.ToLowerInvariant()
    if ($Actual -cne $Entry.Value) { throw "STOP_SOURCE_HASH_MISMATCH_$($Entry.Name)" }
}
if ($Freeze.allocation -cne $Allocation -or $Freeze.docker_image_id -cne $ImageId -or
    ($Freeze.seeds -join ',') -cne $SeedList) { throw 'STOP_FREEZE_IDENTITY_MISMATCH' }
$Output = [IO.Path]::GetFullPath($OutputPath)
if (-not (Test-Path -LiteralPath $Output)) { New-Item -ItemType Directory -Path $Output | Out-Null }
if (Get-ChildItem -LiteralPath $Output -Force) { throw 'STOP_OUTPUT_NOT_EMPTY' }
$Raw = Join-Path $Output 'raw'
New-Item -ItemType Directory -Path $Raw | Out-Null
$Source = $Source.Replace('\','/')
$Raw = (Resolve-Path -LiteralPath $Raw).Path.Replace('\','/')
$Inspect = (& docker image inspect $ImageId --format '{{.Id}} {{.Os}}/{{.Architecture}}' 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $Inspect -cne "$ImageId linux/amd64") { throw 'STOP_IMAGE_ID_MISMATCH' }
$Argv = @('run','--rm','--pull=never','--network=none','--read-only','--cpus=1','--memory=2g','--pids-limit=64',
    '--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
    '--mount',"type=bind,source=$Source,dst=/src,readonly",'--mount',"type=bind,source=$Raw,dst=/out",
    '--workdir','/src','--env','NEEDLE_OUTPUT=/out','--env',"NEEDLE_SEEDS=$SeedList",
    '--env','PYTHONDONTWRITEBYTECODE=1',$ImageId,'runner.py')
$Started = [DateTime]::UtcNow.ToString('o')
$Info = [Diagnostics.ProcessStartInfo]::new(); $Info.FileName = 'docker'; $Info.UseShellExecute = $false
$Info.RedirectStandardOutput = $true; $Info.RedirectStandardError = $true
$Info.Arguments = ($Argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$Process = [Diagnostics.Process]::new(); $Process.StartInfo = $Info
if (-not $Process.Start()) { throw 'STOP_DOCKER_PROCESS_START' }
$StdoutPath = Join-Path $Output 'docker.stdout.bin'; $StderrPath = Join-Path $Output 'docker.stderr.bin'
$Stdout = [IO.File]::Create($StdoutPath); $Stderr = [IO.File]::Create($StderrPath)
$StdoutTask = $Process.StandardOutput.BaseStream.CopyToAsync($Stdout)
$StderrTask = $Process.StandardError.BaseStream.CopyToAsync($Stderr)
$Process.WaitForExit(); $StdoutTask.GetAwaiter().GetResult(); $StderrTask.GetAwaiter().GetResult()
$Stdout.Dispose(); $Stderr.Dispose()
$RawFile = Join-Path $Raw 'formal_result.json'; $Exists = Test-Path -LiteralPath $RawFile
$Receipt = [ordered]@{
    allocation=$Allocation; freeze_sha256=$FreezeSha; image_id=$ImageId; inspected_image=$Inspect
    command_argv=@('docker')+$Argv; start_utc=$Started; end_utc=[DateTime]::UtcNow.ToString('o')
    exit_code=$Process.ExitCode; raw_exists=$Exists
    stdout_bytes=(Get-Item $StdoutPath).Length; stdout_sha256=(Get-FileHash $StdoutPath -Algorithm SHA256).Hash.ToLowerInvariant()
    stderr_bytes=(Get-Item $StderrPath).Length; stderr_sha256=(Get-FileHash $StderrPath -Algorithm SHA256).Hash.ToLowerInvariant()
    raw_bytes=if ($Exists) {(Get-Item $RawFile).Length} else {0}
    raw_sha256=if ($Exists) {(Get-FileHash $RawFile -Algorithm SHA256).Hash.ToLowerInvariant()} else {$null}
    formal_orchestrations=1; retries=0
}
[IO.File]::WriteAllText((Join-Path $Output 'FORMAL_INVOCATION.json'),
    ($Receipt | ConvertTo-Json -Depth 8)+"`n",[Text.UTF8Encoding]::new($false))
if ($Process.ExitCode -ne 0) { throw "STOP_FORMAL_CONTAINER_EXIT_$($Process.ExitCode)" }
if (-not $Exists) { throw 'STOP_FORMAL_RESULT_MISSING' }

param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$ImageId = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$SeedList = '735211,735311,735411'
$Source = (Resolve-Path -LiteralPath $SourcePath).Path
$freezeBytes = [IO.File]::ReadAllBytes((Join-Path $Source 'FREEZE.json'))
$freezeSha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($freezeBytes)).ToLowerInvariant()
$freeze = [Text.Encoding]::UTF8.GetString($freezeBytes) | ConvertFrom-Json
foreach ($entry in $freeze.source_sha256.PSObject.Properties) {
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Source $entry.Name)).Hash.ToLowerInvariant()
    if ($actual -ne $entry.Value) { throw "STOP_SOURCE_HASH_MISMATCH_$($entry.Name)" }
}
if ($freeze.allocation -ne 'needle-online-lora-role-rehearsal-20260927-v1' -or
    $freeze.docker_image_id -ne $ImageId -or ($freeze.seeds -join ',') -ne $SeedList) {
    throw 'STOP_FREEZE_IDENTITY_MISMATCH'
}
$Output = [IO.Path]::GetFullPath($OutputPath)
$Raw = Join-Path $Output 'raw'
if (-not (Test-Path -LiteralPath $Output)) { New-Item -ItemType Directory -Path $Output | Out-Null }
if (Get-ChildItem -LiteralPath $Output -Force) { throw 'STOP_OUTPUT_NOT_EMPTY' }
New-Item -ItemType Directory -Path $Raw | Out-Null
$Source = $Source.Replace('\','/')
$Raw = (Resolve-Path -LiteralPath $Raw).Path.Replace('\','/')
$inspect = (& docker image inspect $ImageId --format '{{.Id}} {{.Os}}/{{.Architecture}}' 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $inspect -ne "$ImageId linux/amd64") { throw 'STOP_IMAGE_ID_MISMATCH' }
$argv = @('run','--rm','--pull=never','--network=none','--read-only','--cpus=1','--memory=2g','--pids-limit=64',
    '--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
    '--mount',"type=bind,source=$Source,dst=/src,readonly",'--mount',"type=bind,source=$Raw,dst=/out",
    '--workdir','/src','--env','NEEDLE_OUTPUT=/out','--env',"NEEDLE_SEEDS=$SeedList",
    '--env','PYTHONDONTWRITEBYTECODE=1',$ImageId,'runner.py')
$started = [DateTime]::UtcNow.ToString('o')
$processInfo = [Diagnostics.ProcessStartInfo]::new()
$processInfo.FileName = 'docker'; $processInfo.UseShellExecute = $false
$processInfo.RedirectStandardOutput = $true; $processInfo.RedirectStandardError = $true
$processInfo.Arguments = ($argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$process = [Diagnostics.Process]::new(); $process.StartInfo = $processInfo
if (-not $process.Start()) { throw 'STOP_DOCKER_PROCESS_START' }
$stdoutPath = Join-Path $Output 'docker.stdout.bin'; $stderrPath = Join-Path $Output 'docker.stderr.bin'
$stdoutStream = [IO.File]::Create($stdoutPath); $stderrStream = [IO.File]::Create($stderrPath)
$stdoutTask = $process.StandardOutput.BaseStream.CopyToAsync($stdoutStream)
$stderrTask = $process.StandardError.BaseStream.CopyToAsync($stderrStream)
$process.WaitForExit(); $stdoutTask.GetAwaiter().GetResult(); $stderrTask.GetAwaiter().GetResult()
$stdoutStream.Dispose(); $stderrStream.Dispose()
$rawFile = Join-Path $Raw 'formal_result.json'
$exists = Test-Path -LiteralPath $rawFile
$receipt = [ordered]@{
    allocation = 'needle-online-lora-role-rehearsal-20260927-v1'; freeze_sha256 = $freezeSha
    image_id = $ImageId; inspected_image = $inspect; command_argv = @('docker') + $argv
    start_utc = $started; end_utc = [DateTime]::UtcNow.ToString('o'); exit_code = $process.ExitCode
    raw_exists = $exists
    stdout_bytes = (Get-Item $stdoutPath).Length; stdout_sha256 = (Get-FileHash $stdoutPath -Algorithm SHA256).Hash.ToLowerInvariant()
    stderr_bytes = (Get-Item $stderrPath).Length; stderr_sha256 = (Get-FileHash $stderrPath -Algorithm SHA256).Hash.ToLowerInvariant()
    raw_bytes = if ($exists) { (Get-Item $rawFile).Length } else { 0 }
    raw_sha256 = if ($exists) { (Get-FileHash $rawFile -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
    formal_orchestrations = 1; retries = 0
}
[IO.File]::WriteAllText((Join-Path $Output 'FORMAL_INVOCATION.json'),
    ($receipt | ConvertTo-Json -Depth 8) + "`n", [Text.UTF8Encoding]::new($false))
if ($process.ExitCode -ne 0) { throw "STOP_FORMAL_CONTAINER_EXIT_$($process.ExitCode)" }
if (-not $exists) { throw 'STOP_FORMAL_RESULT_MISSING' }

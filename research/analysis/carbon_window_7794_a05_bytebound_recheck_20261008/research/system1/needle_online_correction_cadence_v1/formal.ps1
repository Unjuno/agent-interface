param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$ImageId = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$SeedList = '734211,734311,734411'
$Source = (Resolve-Path -LiteralPath $SourcePath).Path
$freezeBytes = [System.IO.File]::ReadAllBytes((Join-Path $Source 'FREEZE.json'))
$freezeSha = [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($freezeBytes)).ToLowerInvariant()
$freeze = [System.Text.Encoding]::UTF8.GetString($freezeBytes) | ConvertFrom-Json
foreach ($entry in $freeze.source_sha256.PSObject.Properties) {
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Source $entry.Name)).Hash.ToLowerInvariant()
    if ($actual -ne $entry.Value) { throw "STOP_SOURCE_HASH_MISMATCH_$($entry.Name)" }
}
if ($freeze.allocation -ne 'needle-online-correction-cadence-20260927-v1' -or
    $freeze.docker_image_id -ne $ImageId -or ($freeze.seeds -join ',') -ne $SeedList) {
    throw 'STOP_FREEZE_IDENTITY_MISMATCH'
}
$Output = [System.IO.Path]::GetFullPath($OutputPath)
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
$start = [DateTime]::UtcNow.ToString('o')
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = 'docker'
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.Arguments = ($argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$proc = [System.Diagnostics.Process]::new()
$proc.StartInfo = $psi
if (-not $proc.Start()) { throw 'STOP_DOCKER_PROCESS_START' }
$stdoutFile = Join-Path $Output 'docker.stdout.bin'
$stderrFile = Join-Path $Output 'docker.stderr.bin'
$stdoutStream = [System.IO.File]::Create($stdoutFile)
$stderrStream = [System.IO.File]::Create($stderrFile)
$stdoutTask = $proc.StandardOutput.BaseStream.CopyToAsync($stdoutStream)
$stderrTask = $proc.StandardError.BaseStream.CopyToAsync($stderrStream)
$proc.WaitForExit()
$stdoutTask.GetAwaiter().GetResult()
$stderrTask.GetAwaiter().GetResult()
$stdoutStream.Dispose()
$stderrStream.Dispose()
$end = [DateTime]::UtcNow.ToString('o')
$rawFile = Join-Path $Raw 'formal_result.json'
$rawExists = Test-Path -LiteralPath $rawFile
$receipt = [ordered]@{
    allocation = 'needle-online-correction-cadence-20260927-v1'
    freeze_sha256 = $freezeSha
    image_id = $ImageId
    inspected_image = $inspect
    command_argv = @('docker') + $argv
    start_utc = $start
    end_utc = $end
    exit_code = $proc.ExitCode
    raw_exists = $rawExists
    stdout_bytes = (Get-Item -LiteralPath $stdoutFile).Length
    stdout_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stdoutFile).Hash.ToLowerInvariant()
    stderr_bytes = (Get-Item -LiteralPath $stderrFile).Length
    stderr_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stderrFile).Hash.ToLowerInvariant()
    raw_bytes = if ($rawExists) { (Get-Item -LiteralPath $rawFile).Length } else { 0 }
    raw_sha256 = if ($rawExists) { (Get-FileHash -Algorithm SHA256 -LiteralPath $rawFile).Hash.ToLowerInvariant() } else { $null }
    formal_orchestrations = 1
    retries = 0
}
$receiptPath = Join-Path $Output 'FORMAL_INVOCATION.json'
[System.IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 8) + "`n", [System.Text.UTF8Encoding]::new($false))
if ($proc.ExitCode -ne 0) { throw "STOP_FORMAL_CONTAINER_EXIT_$($proc.ExitCode)" }
if (-not $rawExists) { throw 'STOP_FORMAL_RESULT_MISSING' }
Get-Content -LiteralPath $stdoutFile -Raw

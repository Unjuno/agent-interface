param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$ImageId = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$Source = (Resolve-Path -LiteralPath $SourcePath).Path.Replace('\','/')
$Output = [System.IO.Path]::GetFullPath($OutputPath)
if (-not (Test-Path -LiteralPath $Output)) { New-Item -ItemType Directory -Path $Output | Out-Null }
if (Get-ChildItem -LiteralPath $Output -Force) { throw 'STOP_CONSTRUCTION_OUTPUT_NOT_EMPTY' }
$Raw = Join-Path $Output 'raw'
New-Item -ItemType Directory -Path $Raw | Out-Null
$Raw = (Resolve-Path -LiteralPath $Raw).Path.Replace('\','/')
$inspect = (& docker image inspect $ImageId --format '{{.Id}} {{.Os}}/{{.Architecture}}' 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $inspect -ne "$ImageId linux/amd64") { throw 'STOP_CONSTRUCTION_IMAGE_ID_MISMATCH' }
$argv = @('run','--rm','--pull=never','--network=none','--read-only','--cpus=1','--memory=2g','--pids-limit=64',
    '--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
    '--mount',"type=bind,source=$Source,dst=/src,readonly",'--mount',"type=bind,source=$Raw,dst=/out",
    '--workdir','/src','--env','NEEDLE_OUTPUT=/out','--env','PYTHONDONTWRITEBYTECODE=1',
    $ImageId,'construction.py')
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = 'docker'; $psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
$psi.Arguments = ($argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$proc = [System.Diagnostics.Process]::new(); $proc.StartInfo = $psi
if (-not $proc.Start()) { throw 'STOP_CONSTRUCTION_PROCESS_START' }
$stdoutFile = Join-Path $Output 'docker.stdout.bin'; $stderrFile = Join-Path $Output 'docker.stderr.bin'
$stdoutStream = [System.IO.File]::Create($stdoutFile); $stderrStream = [System.IO.File]::Create($stderrFile)
$stdoutTask = $proc.StandardOutput.BaseStream.CopyToAsync($stdoutStream)
$stderrTask = $proc.StandardError.BaseStream.CopyToAsync($stderrStream)
$proc.WaitForExit(); $stdoutTask.GetAwaiter().GetResult(); $stderrTask.GetAwaiter().GetResult()
$stdoutStream.Dispose(); $stderrStream.Dispose()
$rawFile = Join-Path $Raw 'construction.json'
$fullRawFile = Join-Path $Raw 'construction_raw.json'
$receipt = [ordered]@{
    seed = 734012; formal_seed = $false; image_id = $ImageId; inspected_image = $inspect
    command_argv = @('docker') + $argv; exit_code = $proc.ExitCode
    stdout_bytes = (Get-Item -LiteralPath $stdoutFile).Length
    stdout_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stdoutFile).Hash.ToLowerInvariant()
    stderr_bytes = (Get-Item -LiteralPath $stderrFile).Length
    stderr_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stderrFile).Hash.ToLowerInvariant()
    raw_bytes = (Get-Item -LiteralPath $rawFile).Length
    raw_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $rawFile).Hash.ToLowerInvariant()
    full_raw_bytes = (Get-Item -LiteralPath $fullRawFile).Length
    full_raw_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $fullRawFile).Hash.ToLowerInvariant()
    formal_orchestrations = 0; optimizer_updates_in_formal = 0
}
[System.IO.File]::WriteAllText((Join-Path $Output 'CONSTRUCTION_INVOCATION.json'),
    ($receipt | ConvertTo-Json -Depth 8) + "`n", [System.Text.UTF8Encoding]::new($false))
if ($proc.ExitCode -ne 0) { throw "STOP_CONSTRUCTION_EXIT_$($proc.ExitCode)" }
Get-Content -LiteralPath $stdoutFile -Raw

param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$FormalOutputPath,
    [Parameter(Mandatory=$true)][string]$AuditOutputPath
)
$ErrorActionPreference = 'Stop'
$ImageId = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$Source = (Resolve-Path -LiteralPath $SourcePath).Path.Replace('\','/')
$Formal = (Resolve-Path -LiteralPath $FormalOutputPath).Path.Replace('\','/')
$Started = [DateTime]::UtcNow.ToString('o')
$Out = [IO.Path]::GetFullPath($AuditOutputPath)
if (-not (Test-Path -LiteralPath $Out)) { New-Item -ItemType Directory -Path $Out | Out-Null }
if (Get-ChildItem -LiteralPath $Out -Force) { throw 'STOP_AUDIT_OUTPUT_NOT_EMPTY' }
$Out = (Resolve-Path -LiteralPath $Out).Path.Replace('\','/')
$inspect = (& docker image inspect $ImageId --format '{{.Id}} {{.Os}}/{{.Architecture}}' 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $inspect -ne "$ImageId linux/amd64") { throw 'STOP_AUDIT_IMAGE_ID_MISMATCH' }
$argv = @('run','--rm','--pull=never','--network=none','--read-only','--cpus=1','--memory=2g','--pids-limit=64',
    '--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
    '--mount',"type=bind,source=$Source,dst=/src,readonly",'--mount',"type=bind,source=$Formal,dst=/in,readonly",
    '--mount',"type=bind,source=$Out,dst=/out",'--workdir','/src',$ImageId,
    'audit.py','/in','/out/AUDIT.json')
$processInfo = [Diagnostics.ProcessStartInfo]::new(); $processInfo.FileName = 'docker'
$processInfo.UseShellExecute = $false; $processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.Arguments = ($argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$process = [Diagnostics.Process]::new(); $process.StartInfo = $processInfo
if (-not $process.Start()) { throw 'STOP_AUDIT_PROCESS_START' }
$stdoutPath = Join-Path $Out 'audit.stdout.bin'; $stderrPath = Join-Path $Out 'audit.stderr.bin'
$stdoutStream = [IO.File]::Create($stdoutPath); $stderrStream = [IO.File]::Create($stderrPath)
$stdoutTask = $process.StandardOutput.BaseStream.CopyToAsync($stdoutStream)
$stderrTask = $process.StandardError.BaseStream.CopyToAsync($stderrStream)
$process.WaitForExit(); $stdoutTask.GetAwaiter().GetResult(); $stderrTask.GetAwaiter().GetResult()
$stdoutStream.Dispose(); $stderrStream.Dispose()
$report = Join-Path $Out 'AUDIT.json'
$receipt = [ordered]@{
    allocation = 'needle-online-lora-role-rehearsal-20260927-v1'; image_id = $ImageId
    inspected_image = $inspect; command_argv = @('docker') + $argv
    start_utc = $Started; end_utc = [DateTime]::UtcNow.ToString('o'); exit_code = $process.ExitCode
    report_exists = (Test-Path -LiteralPath $report)
    report_bytes = if (Test-Path -LiteralPath $report) { (Get-Item $report).Length } else { 0 }
    report_sha256 = if (Test-Path -LiteralPath $report) { (Get-FileHash $report -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
    stdout_bytes = (Get-Item $stdoutPath).Length; stdout_sha256 = (Get-FileHash $stdoutPath -Algorithm SHA256).Hash.ToLowerInvariant()
    stderr_bytes = (Get-Item $stderrPath).Length; stderr_sha256 = (Get-FileHash $stderrPath -Algorithm SHA256).Hash.ToLowerInvariant()
    audit_invocations = 1
}
[IO.File]::WriteAllText((Join-Path $Out 'AUDIT_INVOCATION.json'),
    ($receipt | ConvertTo-Json -Depth 8) + "`n", [Text.UTF8Encoding]::new($false))
if ($process.ExitCode -ne 0) { throw "HOLD_AUDIT_CONTAINER_EXIT_$($process.ExitCode)" }
if (-not (Test-Path -LiteralPath $report)) { throw 'HOLD_AUDIT_REPORT_MISSING' }

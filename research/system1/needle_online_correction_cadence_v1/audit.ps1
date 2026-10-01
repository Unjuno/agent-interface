param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$FormalOutputPath,
    [Parameter(Mandatory=$true)][string]$AuditOutputPath
)
$ErrorActionPreference = 'Stop'
$ImageId = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$Source = (Resolve-Path -LiteralPath $SourcePath).Path.Replace('\','/')
$Formal = (Resolve-Path -LiteralPath $FormalOutputPath).Path.Replace('\','/')
$Out = [System.IO.Path]::GetFullPath($AuditOutputPath)
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
$start = [DateTime]::UtcNow.ToString('o')
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = 'docker'
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.Arguments = ($argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$proc = [System.Diagnostics.Process]::new()
$proc.StartInfo = $psi
if (-not $proc.Start()) { throw 'STOP_AUDIT_PROCESS_START' }
$stdoutFile = Join-Path $Out 'audit.stdout.bin'
$stderrFile = Join-Path $Out 'audit.stderr.bin'
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
$report = Join-Path $Out 'AUDIT.json'
$receipt = [ordered]@{
    allocation = 'needle-online-correction-cadence-20260927-v1'
    image_id = $ImageId
    inspected_image = $inspect
    command_argv = @('docker') + $argv
    start_utc = $start
    end_utc = $end
    exit_code = $proc.ExitCode
    report_exists = (Test-Path -LiteralPath $report)
    report_bytes = if (Test-Path -LiteralPath $report) { (Get-Item -LiteralPath $report).Length } else { 0 }
    report_sha256 = if (Test-Path -LiteralPath $report) { (Get-FileHash -Algorithm SHA256 -LiteralPath $report).Hash.ToLowerInvariant() } else { $null }
    stdout_bytes = (Get-Item -LiteralPath $stdoutFile).Length
    stdout_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stdoutFile).Hash.ToLowerInvariant()
    stderr_bytes = (Get-Item -LiteralPath $stderrFile).Length
    stderr_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stderrFile).Hash.ToLowerInvariant()
    audit_invocations = 1
}
$receiptPath = Join-Path $Out 'AUDIT_INVOCATION.json'
[System.IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 8) + "`n", [System.Text.UTF8Encoding]::new($false))
if ($proc.ExitCode -ne 0) { throw "HOLD_AUDIT_CONTAINER_EXIT_$($proc.ExitCode)" }
if (-not (Test-Path -LiteralPath $report)) { throw 'HOLD_AUDIT_REPORT_MISSING' }
Get-Content -LiteralPath $stdoutFile -Raw

param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$FormalOutputPath,
    [Parameter(Mandatory=$true)][string]$AuditOutputPath
)
$ErrorActionPreference = 'Stop'
$Allocation = 'needle-role-router-online-lora-replay-20260927-v1'
$ImageId = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$Source = (Resolve-Path -LiteralPath $SourcePath).Path.Replace('\','/')
$Formal = (Resolve-Path -LiteralPath $FormalOutputPath).Path.Replace('\','/')
$Output = [IO.Path]::GetFullPath($AuditOutputPath)
if (-not (Test-Path -LiteralPath $Output)) { New-Item -ItemType Directory -Path $Output | Out-Null }
if (Get-ChildItem -LiteralPath $Output -Force) { throw 'STOP_AUDIT_OUTPUT_NOT_EMPTY' }
$Output = (Resolve-Path -LiteralPath $Output).Path.Replace('\','/')
$Inspect = (& docker image inspect $ImageId --format '{{.Id}} {{.Os}}/{{.Architecture}}' 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $Inspect -cne "$ImageId linux/amd64") { throw 'STOP_AUDIT_IMAGE_ID_MISMATCH' }
$Argv = @('run','--rm','--pull=never','--network=none','--read-only','--cpus=1','--memory=2g','--pids-limit=64',
    '--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
    '--mount',"type=bind,source=$Source,dst=/src,readonly",'--mount',"type=bind,source=$Formal,dst=/in,readonly",
    '--mount',"type=bind,source=$Output,dst=/out",'--workdir','/src',$ImageId,'audit.py','/in','/out/AUDIT.json')
$Started = [DateTime]::UtcNow.ToString('o')
$Info = [Diagnostics.ProcessStartInfo]::new(); $Info.FileName = 'docker'; $Info.UseShellExecute = $false
$Info.RedirectStandardOutput = $true; $Info.RedirectStandardError = $true
$Info.Arguments = ($Argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$Process = [Diagnostics.Process]::new(); $Process.StartInfo = $Info
if (-not $Process.Start()) { throw 'STOP_AUDIT_PROCESS_START' }
$StdoutPath=Join-Path $Output 'audit.stdout.bin'; $StderrPath=Join-Path $Output 'audit.stderr.bin'
$Stdout=[IO.File]::Create($StdoutPath); $Stderr=[IO.File]::Create($StderrPath)
$StdoutTask=$Process.StandardOutput.BaseStream.CopyToAsync($Stdout)
$StderrTask=$Process.StandardError.BaseStream.CopyToAsync($Stderr)
$Process.WaitForExit(); $StdoutTask.GetAwaiter().GetResult(); $StderrTask.GetAwaiter().GetResult()
$Stdout.Dispose(); $Stderr.Dispose()
$Report=Join-Path $Output 'AUDIT.json'; $Exists=Test-Path -LiteralPath $Report
$Receipt=[ordered]@{
    allocation=$Allocation; image_id=$ImageId; inspected_image=$Inspect; command_argv=@('docker')+$Argv
    start_utc=$Started; end_utc=[DateTime]::UtcNow.ToString('o'); exit_code=$Process.ExitCode
    report_exists=$Exists; report_bytes=if ($Exists) {(Get-Item $Report).Length} else {0}
    report_sha256=if ($Exists) {(Get-FileHash $Report -Algorithm SHA256).Hash.ToLowerInvariant()} else {$null}
    stdout_bytes=(Get-Item $StdoutPath).Length; stdout_sha256=(Get-FileHash $StdoutPath -Algorithm SHA256).Hash.ToLowerInvariant()
    stderr_bytes=(Get-Item $StderrPath).Length; stderr_sha256=(Get-FileHash $StderrPath -Algorithm SHA256).Hash.ToLowerInvariant()
    audit_invocations=1
}
[IO.File]::WriteAllText((Join-Path $Output 'AUDIT_INVOCATION.json'),
    ($Receipt | ConvertTo-Json -Depth 8)+"`n",[Text.UTF8Encoding]::new($false))
if ($Process.ExitCode -ne 0) { throw "HOLD_AUDIT_CONTAINER_EXIT_$($Process.ExitCode)" }
if (-not $Exists) { throw 'HOLD_AUDIT_REPORT_MISSING' }

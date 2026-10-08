param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$ConstructionRawPath,
    [Parameter(Mandatory=$true)][string]$AuditOutputPath
)
$ErrorActionPreference = 'Stop'
$ImageId = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$Source = (Resolve-Path -LiteralPath $SourcePath).Path.Replace('\','/')
$Raw = (Resolve-Path -LiteralPath $ConstructionRawPath).Path.Replace('\','/')
$Out = [System.IO.Path]::GetFullPath($AuditOutputPath)
if (-not (Test-Path -LiteralPath $Out)) { New-Item -ItemType Directory -Path $Out | Out-Null }
if (Get-ChildItem -LiteralPath $Out -Force) { throw 'STOP_CONSTRUCTION_AUDIT_OUTPUT_NOT_EMPTY' }
$Out = (Resolve-Path -LiteralPath $Out).Path.Replace('\','/')
$argv = @('run','--rm','--pull=never','--network=none','--read-only','--cpus=1','--memory=2g','--pids-limit=64',
    '--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
    '--mount',"type=bind,source=$Source,dst=/src,readonly",'--mount',"type=bind,source=$Raw,dst=/in,readonly",
    '--mount',"type=bind,source=$Out,dst=/out",'--workdir','/src',$ImageId,
    'construction_audit.py','/in/construction_raw.json','/out/CONSTRUCTION_AUDIT.json')
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = 'docker'; $psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
$psi.Arguments = ($argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$proc = [System.Diagnostics.Process]::new(); $proc.StartInfo = $psi
if (-not $proc.Start()) { throw 'STOP_CONSTRUCTION_AUDIT_PROCESS_START' }
$stdoutFile = Join-Path $Out 'audit.stdout.bin'; $stderrFile = Join-Path $Out 'audit.stderr.bin'
$stdoutStream = [System.IO.File]::Create($stdoutFile); $stderrStream = [System.IO.File]::Create($stderrFile)
$stdoutTask = $proc.StandardOutput.BaseStream.CopyToAsync($stdoutStream)
$stderrTask = $proc.StandardError.BaseStream.CopyToAsync($stderrStream)
$proc.WaitForExit(); $stdoutTask.GetAwaiter().GetResult(); $stderrTask.GetAwaiter().GetResult()
$stdoutStream.Dispose(); $stderrStream.Dispose()
$report = Join-Path $Out 'CONSTRUCTION_AUDIT.json'
$receipt = [ordered]@{
    seed = 734014; formal = $false; image_id = $ImageId
    command_argv = @('docker') + $argv; exit_code = $proc.ExitCode
    report_exists = (Test-Path -LiteralPath $report)
    report_bytes = (Get-Item -LiteralPath $report).Length
    report_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $report).Hash.ToLowerInvariant()
    stdout_bytes = (Get-Item -LiteralPath $stdoutFile).Length
    stdout_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stdoutFile).Hash.ToLowerInvariant()
    stderr_bytes = (Get-Item -LiteralPath $stderrFile).Length
    stderr_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stderrFile).Hash.ToLowerInvariant()
    audit_invocations = 1
}
[System.IO.File]::WriteAllText((Join-Path $Out 'CONSTRUCTION_AUDIT_INVOCATION.json'),
    ($receipt | ConvertTo-Json -Depth 8) + "`n", [System.Text.UTF8Encoding]::new($false))
if ($proc.ExitCode -ne 0) { throw "HOLD_CONSTRUCTION_AUDIT_EXIT_$($proc.ExitCode)" }
Get-Content -LiteralPath $stdoutFile -Raw

param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$ImageId = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$Allocation = 'needle-role-router-online-lora-replay-20260927-v1'
$Seed = 736014
$Source = (Resolve-Path -LiteralPath $SourcePath).Path.Replace('\','/')
$Out = [IO.Path]::GetFullPath($OutputPath)
$Started = [DateTime]::UtcNow.ToString('o')
if (-not (Test-Path -LiteralPath $Out)) { New-Item -ItemType Directory -Path $Out | Out-Null }
if (Get-ChildItem -LiteralPath $Out -Force) { throw 'STOP_CONSTRUCTION_OUTPUT_NOT_EMPTY' }
New-Item -ItemType Directory -Path (Join-Path $Out 'raw') | Out-Null
$Out = (Resolve-Path -LiteralPath $Out).Path.Replace('\','/')
$argv = @('run','--rm','--pull=never','--network=none','--read-only','--cpus=1','--memory=2g','--pids-limit=64',
    '--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
    '--mount',"type=bind,source=$Source,dst=/src,readonly",'--mount',"type=bind,source=$Out,dst=/out",
    '--workdir','/src','--env','NEEDLE_CONSTRUCTION_OUTPUT=/out/raw','--env','PYTHONDONTWRITEBYTECODE=1',
    $ImageId,'construction.py')
$processInfo = [Diagnostics.ProcessStartInfo]::new(); $processInfo.FileName = 'docker'
$processInfo.UseShellExecute = $false; $processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.Arguments = ($argv | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$proc = [Diagnostics.Process]::new(); $proc.StartInfo = $processInfo
if (-not $proc.Start()) { throw 'STOP_CONSTRUCTION_PROCESS_START' }
$stdout = [IO.File]::Create((Join-Path $Out 'docker.stdout.bin'))
$stderr = [IO.File]::Create((Join-Path $Out 'docker.stderr.bin'))
$stdoutTask = $proc.StandardOutput.BaseStream.CopyToAsync($stdout)
$stderrTask = $proc.StandardError.BaseStream.CopyToAsync($stderr)
$proc.WaitForExit(); $stdoutTask.GetAwaiter().GetResult(); $stderrTask.GetAwaiter().GetResult()
$stdout.Dispose(); $stderr.Dispose()
$Raw = Join-Path $Out 'raw\construction_raw.json'
$Receipt = [ordered]@{allocation=$Allocation; seed=$Seed; image_id=$ImageId; inspected_image="$ImageId linux/amd64"
    command_argv=@('docker')+$argv; start_utc=$Started; end_utc=[DateTime]::UtcNow.ToString('o')
    exit_code=$proc.ExitCode; raw_exists=(Test-Path -LiteralPath $Raw)
    stdout_bytes=(Get-Item (Join-Path $Out 'docker.stdout.bin')).Length
    stdout_sha256=(Get-FileHash (Join-Path $Out 'docker.stdout.bin') -Algorithm SHA256).Hash.ToLowerInvariant()
    stderr_bytes=(Get-Item (Join-Path $Out 'docker.stderr.bin')).Length
    stderr_sha256=(Get-FileHash (Join-Path $Out 'docker.stderr.bin') -Algorithm SHA256).Hash.ToLowerInvariant()
    raw_bytes=if (Test-Path -LiteralPath $Raw) {(Get-Item $Raw).Length} else {0}
    raw_sha256=if (Test-Path -LiteralPath $Raw) {(Get-FileHash $Raw -Algorithm SHA256).Hash.ToLowerInvariant()} else {$null}
    construction_orchestrations=1; retries=0}
[IO.File]::WriteAllText((Join-Path $Out 'CONSTRUCTION_INVOCATION.json'),
    ($Receipt|ConvertTo-Json -Depth 8)+"`n",[Text.UTF8Encoding]::new($false))
if ($proc.ExitCode -ne 0) { throw "STOP_CONSTRUCTION_EXIT_$($proc.ExitCode)" }

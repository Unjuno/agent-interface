param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('construction02','producer-a02','audit-a02')]
  [string]$Phase
)
$ErrorActionPreference = 'Stop'
$studyRoot = $PSScriptRoot
$studyExecution = Join-Path $studyRoot 'execution'
$studyReceiptDir = Join-Path $studyExecution $Phase
if (Test-Path -LiteralPath $studyReceiptDir) { throw "Existing receipt directory: no retry or overwrite" }
$studyImage = 'sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4'
$studyArgs = @('run','--rm','--pull','never','--network','none','--cpus','0.25','--memory','512m','--user','65534:65534','--env','PYTHONDONTWRITEBYTECODE=1')
if ($Phase -eq 'producer-a02') {
  $studyMount = Join-Path (Split-Path $studyRoot -Parent) 'appserver-journal-composition-4d74-a02-candidate-input'
  if (-not (Test-Path -LiteralPath $studyMount)) { throw "Candidate source staging missing" }
} else { $studyMount = $studyRoot }
$studyArgs += @('--volume',($studyMount + ':/src:ro'),'--workdir','/src')
if ($Phase -ne 'construction02') {
  $studyOutput = Join-Path $studyReceiptDir 'output'
  $studyArgs += @('--volume',($studyOutput + ':/out'))
}
if ($Phase -eq 'construction02') {
  $studyArgs += @($studyImage,'python','-B','/src/construction_checks.py','--fixture','/src/fixture.json')
} elseif ($Phase -eq 'producer-a02') {
  $studyArgs += @($studyImage,'python','-B','/src/producer.py','--fixture','/src/fixture.json','--out','/out/raw.json')
} else {
  $studySaved = Join-Path (Join-Path $studyExecution 'producer-a02') 'output'
  if (-not (Test-Path -LiteralPath (Join-Path $studySaved 'raw.json'))) { throw "First producer raw missing" }
  $studyArgs += @('--volume',($studySaved + ':/results:ro'),$studyImage,'python','-B','/src/auditor.py','--fixture','/src/fixture.json','--raw','/results/raw.json','--source-dir','/src','--out','/out/audit.json')
}
[IO.Directory]::CreateDirectory($studyReceiptDir) | Out-Null
if ($Phase -ne 'construction02') { [IO.Directory]::CreateDirectory($studyOutput) | Out-Null }
$studyUtf8 = New-Object Text.UTF8Encoding($false)
$studyInfo = New-Object Diagnostics.ProcessStartInfo
$studyInfo.FileName = (Get-Command wslc).Source
$studyInfo.UseShellExecute = $false
$studyInfo.CreateNoWindow = $true
$studyInfo.RedirectStandardOutput = $true
$studyInfo.RedirectStandardError = $true
$studyInfo.Arguments = (($studyArgs | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' ')
$studyReceipt = [ordered]@{schema='issue59-host-command-receipt-v1';phase=$Phase;argv=@($studyInfo.FileName)+$studyArgs;started_utc=[DateTime]::UtcNow.ToString('o');finished_utc=$null;host_pid=$PID;wslc_client_pid=$null;exit_code=$null;console_log_encoding='UTF-8 host-decoded text';source_mount_readonly=$true}
[IO.File]::WriteAllText((Join-Path $studyReceiptDir 'command.json'),($studyReceipt | ConvertTo-Json -Depth 8),$studyUtf8)
$studyProc = New-Object Diagnostics.Process
$studyProc.StartInfo = $studyInfo
[void]$studyProc.Start()
$studyReceipt.wslc_client_pid = $studyProc.Id
$studyStdoutTask = $studyProc.StandardOutput.ReadToEndAsync()
$studyStderrTask = $studyProc.StandardError.ReadToEndAsync()
$studyProc.WaitForExit()
$studyStdout = $studyStdoutTask.GetAwaiter().GetResult()
$studyStderr = $studyStderrTask.GetAwaiter().GetResult()
[IO.File]::WriteAllText((Join-Path $studyReceiptDir 'stdout.log'),$studyStdout,$studyUtf8)
[IO.File]::WriteAllText((Join-Path $studyReceiptDir 'stderr.log'),$studyStderr,$studyUtf8)
$studyReceipt.exit_code = $studyProc.ExitCode
$studyReceipt.finished_utc = [DateTime]::UtcNow.ToString('o')
[IO.File]::WriteAllText((Join-Path $studyReceiptDir 'command.json'),($studyReceipt | ConvertTo-Json -Depth 8),$studyUtf8)
Write-Output ($studyReceipt | ConvertTo-Json -Depth 8 -Compress)
Write-Output $studyStdout
if ($studyStderr) { Write-Output $studyStderr }
exit $studyProc.ExitCode

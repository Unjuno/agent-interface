param(
  [Parameter(Mandatory)][string]$RawPath,
  [Parameter(Mandatory)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$Source = (Resolve-Path -LiteralPath $PSScriptRoot).Path.Replace('\','/')
$Raw = (Resolve-Path -LiteralPath $RawPath).Path.Replace('\','/')
$Output = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $Output) { throw 'STOP_OUTPUT_ALREADY_EXISTS' }
New-Item -ItemType Directory -Path $Output | Out-Null
$FrozenAuditPath = Join-Path $Source 'FROZEN_AUDIT_ORIGINAL.py'
$CorrectedAuditPath = Join-Path $Source 'audit.py'
$FrozenAudit = [IO.File]::ReadAllText($FrozenAuditPath)
$CorrectedAudit = [IO.File]::ReadAllText($CorrectedAuditPath)
$OldAllocation = 'needle-intent-capacity-4679-v1'
$NewAllocation = 'needle-intent-capacity-4679-v2'
$OldCount = [regex]::Matches($FrozenAudit,[regex]::Escape($OldAllocation)).Count
$FrozenAuditHash = (Get-FileHash -LiteralPath $FrozenAuditPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($OldCount -ne 1 -or $FrozenAuditHash -cne '859991d9e7496681bb786b9bca35ef2f7644180b5d108be636eea9f664935156' -or
    $CorrectedAudit -cne $FrozenAudit.Replace($OldAllocation,$NewAllocation)) { throw 'STOP_AUDIT_SOURCE_DIFF_NOT_SINGLE_LITERAL' }
$Image = 'sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e'
$Inspect = (& docker image inspect $Image --format '{{.Id}} {{.Os}}/{{.Architecture}}' 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $Inspect -cne "$Image linux/amd64") { throw 'STOP_IMAGE_ID_OR_PLATFORM' }
$ExpectedRaw = @{
  'seed_4153201.json'='efc40b1776f9df4be05ee2518af7552b5ccd6c4d24acc5e3737dc4a545b59ee1'
  'seed_4153203.json'='8128339b66fa330f19d0ba6e661fa8de065ef6b9b2d862b92862af7f0a87e32f'
  'seed_4153207.json'='4fb34391efee50bd7d1991e4595bf1348ff5027eb25d6488c556c2e3b9660aed'
}
$Before = @{}
foreach ($Name in $ExpectedRaw.Keys) {
  $File = Join-Path $Raw $Name
  if (-not (Test-Path -LiteralPath $File)) { throw "STOP_RAW_MISSING_$Name" }
  $Hash = (Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($Hash -cne $ExpectedRaw[$Name]) { throw "STOP_RAW_HASH_$Name" }
  $Before[$Name] = $Hash
}
$Argv = @('run','--rm','--name','unjuno-needle-intent-capacity-4778-audit-recheck-20260928',
  '--pull=never','--network=none','--read-only','--cpus=1','--memory=2g','--pids-limit=64',
  '--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
  '--env','HOME=/tmp','--env','XDG_CACHE_HOME=/tmp',
  '--mount',"type=bind,source=$Source,dst=/src,readonly",
  '--mount',"type=bind,source=$Raw,dst=/raw,readonly",
  '--mount',"type=bind,source=$($Output.Replace('\','/')),dst=/out",
  '--workdir','/src',$Image,'python','-B','/src/audit.py','--raw','/raw','--out','/out/AUDIT.json')
$SourceHash = (Get-FileHash -LiteralPath (Join-Path $Source 'audit.py') -Algorithm SHA256).Hash.ToLowerInvariant()
$Started = [DateTime]::UtcNow.ToString('o')
$Info = [Diagnostics.ProcessStartInfo]::new()
$Info.FileName = 'docker'
$Info.UseShellExecute = $false
$Info.RedirectStandardOutput = $true
$Info.RedirectStandardError = $true
foreach ($Arg in $Argv) { [void]$Info.ArgumentList.Add($Arg) }
$ProcessObj = [Diagnostics.Process]::new()
$ProcessObj.StartInfo = $Info
if (-not $ProcessObj.Start()) { throw 'STOP_DOCKER_PROCESS_START' }
$StdoutPath = Join-Path $Output 'docker.stdout.bin'
$StderrPath = Join-Path $Output 'docker.stderr.bin'
$Stdout = [IO.File]::Create($StdoutPath)
$Stderr = [IO.File]::Create($StderrPath)
$StdoutTask = $ProcessObj.StandardOutput.BaseStream.CopyToAsync($Stdout)
$StderrTask = $ProcessObj.StandardError.BaseStream.CopyToAsync($Stderr)
$ProcessObj.WaitForExit()
$StdoutTask.GetAwaiter().GetResult()
$StderrTask.GetAwaiter().GetResult()
$Stdout.Dispose()
$Stderr.Dispose()
$After = @{}
foreach ($Name in $ExpectedRaw.Keys) {
  $Hash = (Get-FileHash -LiteralPath (Join-Path $Raw $Name) -Algorithm SHA256).Hash.ToLowerInvariant()
  $After[$Name] = $Hash
  if ($Hash -cne $Before[$Name]) { throw "STOP_RAW_CHANGED_$Name" }
}
$AuditPath = Join-Path $Output 'AUDIT.json'
$AuditExists = Test-Path -LiteralPath $AuditPath
$Receipt = [ordered]@{
  scope='audit-only; formal trainer invocation count 0'
  issue=4778
  original_audit_blob_sha1='d9d058e50e8c25bb4b88967668433026229a9d5c'
  original_source_sha256=$FrozenAuditHash
  corrected_source_path='research/system1/needle_intent_capacity_4679_v2/audit_only_recheck_20260928/audit.py'
  correction='single allocation-identity literal v1 -> v2; all gates and thresholds unchanged'
  corrected_audit_sha256=$SourceHash
  image_id=$Image
  inspected_image=$Inspect
  command_argv=@('docker')+$Argv
  start_utc=$Started
  end_utc=[DateTime]::UtcNow.ToString('o')
  exit_code=$ProcessObj.ExitCode
  stdout_bytes=(Get-Item -LiteralPath $StdoutPath).Length
  stdout_sha256=(Get-FileHash -LiteralPath $StdoutPath -Algorithm SHA256).Hash.ToLowerInvariant()
  stderr_bytes=(Get-Item -LiteralPath $StderrPath).Length
  stderr_sha256=(Get-FileHash -LiteralPath $StderrPath -Algorithm SHA256).Hash.ToLowerInvariant()
  raw_before=$Before
  raw_after=$After
  audit_exists=$AuditExists
  audit_bytes=if ($AuditExists) {(Get-Item -LiteralPath $AuditPath).Length} else {0}
  audit_sha256=if ($AuditExists) {(Get-FileHash -LiteralPath $AuditPath -Algorithm SHA256).Hash.ToLowerInvariant()} else {$null}
  no_training=true
}
[IO.File]::WriteAllText((Join-Path $Output 'AUDIT_INVOCATION.json'),($Receipt | ConvertTo-Json -Depth 6)+"`n",[Text.UTF8Encoding]::new($false))
if ($ProcessObj.ExitCode -ne 0) { exit $ProcessObj.ExitCode }
if (-not $AuditExists) { throw 'STOP_AUDIT_OUTPUT_MISSING' }

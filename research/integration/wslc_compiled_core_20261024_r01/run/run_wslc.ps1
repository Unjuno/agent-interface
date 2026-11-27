$ErrorActionPreference = 'Stop'
$runDir = [System.IO.Path]::GetFullPath($PSScriptRoot)
$packetRoot = [System.IO.Path]::GetFullPath((Join-Path $runDir '..'))
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $runDir '..\..\..\..'))
$rawDir = Join-Path $runDir 'raw'
$conditionsPath = Join-Path $packetRoot 'conditions.json'
$conditions = Get-Content -LiteralPath $conditionsPath -Raw | ConvertFrom-Json
$gitHead = (& git -C $repoRoot rev-parse HEAD).Trim()
if ($gitHead -ne $conditions.source_commit) { throw "source commit changed: $gitHead" }
$sourceFiles = @(
    @{ path = 'runtime\core_v1\test_compiled_gui.py'; expected = $conditions.source_sha256.test_compiled_gui_py },
    @{ path = 'runtime\core_v1\test_compiled_release_recovery_01a0ff35.py'; expected = $conditions.source_sha256.test_compiled_release_recovery_01a0ff35_py },
    @{ path = 'runtime\core_v1\compiled_gui.py'; expected = $conditions.source_sha256.compiled_gui_py }
)
foreach ($source in $sourceFiles) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $repoRoot $source.path) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $source.expected) { throw "frozen source hash mismatch: $($source.path)" }
}
$modulePath = Join-Path $repoRoot '.github\scripts\wslc_bounded_process.psm1'
$moduleHash = (Get-FileHash -LiteralPath $modulePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($moduleHash -ne $conditions.source_sha256.wslc_bounded_process_psm1) { throw 'bounded runner module hash changed' }
$runnerHash = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($runnerHash -ne $conditions.source_sha256.run_wslc_ps1) { throw 'runner source hash changed' }
$wslc = Get-Command wslc.exe -ErrorAction Stop
if ($wslc.Source -ne $conditions.environment.wslc_executable) { throw "unexpected WSLc executable: $($wslc.Source)" }
Import-Module $modulePath -Force
function Invoke-RecordedWslc {
    param([string[]]$Arguments, [int]$TimeoutSeconds, [string]$Prefix)
    $result = Invoke-WslcBoundedProcess -FilePath $wslc.Source -ArgumentList $Arguments -TimeoutSeconds $TimeoutSeconds
    [System.IO.File]::WriteAllText((Join-Path $rawDir "$Prefix.stdout.txt"), $result.StandardOutput, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText((Join-Path $rawDir "$Prefix.stderr.txt"), $result.StandardError, [System.Text.UTF8Encoding]::new($false))
    return $result
}
$imageInfoResult = Invoke-RecordedWslc -Arguments @('inspect','--type','image',$conditions.environment.image_tag,'--format','json') -TimeoutSeconds $conditions.limits.cleanup_query_timeout_seconds -Prefix 'selected-image-inspect'
if ($imageInfoResult.TimedOut -or $imageInfoResult.ExitCode -ne 0) { throw 'selected-image inspection failed before container launch' }
$imageInfo = @(ConvertFrom-Json -InputObject $imageInfoResult.StandardOutput -ErrorAction Stop)
if ($imageInfo.Count -ne 1 -or $imageInfo[0].Id -ne $conditions.environment.image_id) { throw 'selected WSLc image ID changed; refused before container launch' }
$startedUtc = [DateTime]::UtcNow.ToString('o')
$containerName = $conditions.allocation.container_name
$cidPath = Join-Path $runDir 'container.cid'
if (Test-Path -LiteralPath $cidPath) { throw 'refusing to overwrite existing container CID receipt' }
$volumeSource = "${repoRoot}:/workspace:ro"
$resultsSource = "${rawDir}:/results:rw"
$runArguments = @('run','--rm','--name',$containerName,'--cidfile',$cidPath,'--pull','never','--network','none','--memory','768M','--cpus','1','--stop-timeout','5','--volume',$volumeSource,'--volume',$resultsSource,'--workdir','/workspace','--env','AGENT_INTERFACE_FAKE_X_COMPOSITION_RAW_DIR=/results',$conditions.environment.image_tag,'python3','-B','-m','unittest','-v')
foreach ($selector in $conditions.test.unittest_selectors) { $runArguments += $selector }
$runResult = Invoke-RecordedWslc -Arguments $runArguments -TimeoutSeconds $conditions.limits.run_timeout_seconds -Prefix 'wslc-run'
$cid = $null
if (Test-Path -LiteralPath $cidPath -PathType Leaf) { $cid = (Get-Content -LiteralPath $cidPath -Raw).Trim() }
$validCid = $cid -match '^[0-9a-fA-F]{64}$'
$cleanup = [ordered]@{ attempted = $false; status = 'not_attempted_no_valid_cid'; matched_entries = $null; exit_code = $null; timed_out = $false; stdout_file = $null; stderr_file = $null }
if ($validCid) {
    $cleanup.attempted = $true
    $cleanupResult = Invoke-RecordedWslc -Arguments @('container','list','--all','--filter',"id=$cid",'--format','json') -TimeoutSeconds $conditions.limits.cleanup_query_timeout_seconds -Prefix 'exact-cid-cleanup-query'
    $cleanup.exit_code = $cleanupResult.ExitCode
    $cleanup.timed_out = $cleanupResult.TimedOut
    $cleanup.stdout_file = 'raw/exact-cid-cleanup-query.stdout.txt'
    $cleanup.stderr_file = 'raw/exact-cid-cleanup-query.stderr.txt'
    $listing = ($cleanupResult.StandardOutput -split "`r?`n" -join "`n").Trim()
    if ($cleanupResult.TimedOut) { $cleanup.status = 'unknown_query_timeout' }
    elseif ($cleanupResult.ExitCode -ne 0) { $cleanup.status = 'unknown_query_error' }
    elseif ([string]::IsNullOrWhiteSpace($listing) -or $listing -match '^\[\s*\]$') { $cleanup.status = 'absent'; $cleanup.matched_entries = 0 }
    else {
        try { $items = @(ConvertFrom-Json -InputObject $listing -ErrorAction Stop); $cleanup.matched_entries = $items.Count; if ($items.Count -eq 0) { $cleanup.status = 'absent' } else { $cleanup.status = 'still_present' } }
        catch { $cleanup.status = 'unknown_invalid_json' }
    }
}
$record = [ordered]@{
    schema = 'wslc-compiled-core-r01-run-v1'
    attempt_id = $conditions.attempt_id
    started_utc = $startedUtc
    ended_utc = [DateTime]::UtcNow.ToString('o')
    executable = $wslc.Source
    source_commit = $gitHead
    command_arguments = $runArguments
    runner_process_id = $runResult.ProcessId
    timed_out = $runResult.TimedOut
    exit_code = $runResult.ExitCode
    selected_image_id = $imageInfo[0].Id
    full_container_id = if ($validCid) { $cid } else { $null }
    cid_receipt_present = Test-Path -LiteralPath $cidPath -PathType Leaf
    cleanup = $cleanup
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runDir 'runtime.json') -Encoding utf8
if ($runResult.TimedOut) { throw 'one-shot WSLc invocation timed out; outcome is UNKNOWN; do not retry' }
if ($runResult.ExitCode -ne 0) { throw "one-shot WSLc invocation exited $($runResult.ExitCode); no retry" }
if (-not $validCid) { throw 'WSLc did not produce a valid 64-hex CID receipt; outcome is UNKNOWN; no retry' }
if ($cleanup.status -ne 'absent') { throw "exact-CID cleanup is $($cleanup.status); outcome is UNKNOWN; preserve this attempt and do not retry" }

$ErrorActionPreference = 'Stop'
$package = $PSScriptRoot
$out = Join-Path $package 'results/current-head-4158-run02'
$manifest = Get-Content (Join-Path $package 'source-manifest.json') -Raw | ConvertFrom-Json -AsHashtable
$status = Get-Content (Join-Path $out 'run-status.json') -Raw | ConvertFrom-Json -AsHashtable
$failures = [System.Collections.Generic.List[string]]::new()
$checks = [System.Collections.Generic.List[object]]::new()

function Add-Check([string]$Name, [bool]$Pass, $Details = $null) {
    $checks.Add(@{ name = $Name; pass = $Pass; details = $Details })
    if (-not $Pass) { $failures.Add($Name) }
}
function Hash-File([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Normalize-Path([string]$Path) { $Path.Replace('\', '/') }

$snapshotFailures = [System.Collections.Generic.List[string]]::new()
$materializedFailures = [System.Collections.Generic.List[string]]::new()
foreach ($entry in $manifest.files.GetEnumerator()) {
    $relative = [string]$entry.Key
    $expected = $entry.Value
    $snapshot = Join-Path $package ("source-snapshots/" + $relative + '.txt')
    $materialized = Join-Path (Join-Path $out 'source') $relative
    if (-not (Test-Path -LiteralPath $snapshot) -or
        (Hash-File $snapshot) -ne $expected.sha256 -or
        (Get-Item -LiteralPath $snapshot).Length -ne $expected.bytes) {
        $snapshotFailures.Add($relative)
    }
    if (-not (Test-Path -LiteralPath $materialized) -or
        (Hash-File $materialized) -ne $expected.sha256 -or
        (Get-Item -LiteralPath $materialized).Length -ne $expected.bytes) {
        $materializedFailures.Add($relative)
    }
}
Add-Check 'all_56_frozen_snapshots_match_manifest' ($snapshotFailures.Count -eq 0) $snapshotFailures.ToArray()
Add-Check 'all_56_materialized_sources_match_manifest' ($materializedFailures.Count -eq 0) $materializedFailures.ToArray()
Add-Check 'candidate_source_ref_is_exact_head' ($manifest.ref -eq '4158d9b063e7cbf56828f1b0667ec2714af0ff2b') $manifest.ref

$expectedOwners = @{
    'v12-perkey' = 'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py'
    'v15-default' = 'research/live_control/input_transition_owner_v4.py'
    'v15-perkey' = 'research/live_control/input_owner_v12.py'
}
$routes = @{}
$routeStatusOk = $status.Count -eq 3
foreach ($row in $status) {
    if ($row.exit_code -ne 0) { $routeStatusOk = $false }
}
Add-Check 'all_three_route_probes_reached_exit_zero' $routeStatusOk $status

foreach ($route in @('v12-perkey', 'v15-default', 'v15-perkey')) {
    $resultPath = Join-Path (Join-Path $out $route) 'result.json'
    $stdoutPath = Join-Path $out ($route + '.stdout.txt')
    $stderrPath = Join-Path $out ($route + '.stderr.txt')
    $result = Get-Content $resultPath -Raw | ConvertFrom-Json -AsHashtable
    $stdout = Get-Content $stdoutPath -Raw | ConvertFrom-Json -AsHashtable
    $stderrEmpty = (Get-Item -LiteralPath $stderrPath).Length -eq 0
    $ownerFile = Normalize-Path ([string]$result.owner_file)
    $ownerManifestRecord = $manifest.files[$ownerFile]
    $actualOwnerHashMatches = ($null -ne $ownerManifestRecord -and
                               $ownerManifestRecord.sha256 -eq $result.owner_sha256)
    $stdoutMatches = $stdout.route -eq $result.route -and
                     $stdout.owner_file -eq $result.owner_file -and
                     $stdout.owner_sha256 -eq $result.owner_sha256 -and
                     $stdout.owner_matches_a01 -eq $result.owner_matches_a01 -and
                     $stdout.session_started -eq $result.session_started -and
                     $stdout.owner_instantiated -eq $result.owner_instantiated
    $atBoundary = $result.route -eq $route -and
                  $result.source_selection_finished -eq $true -and
                  $result.session_started -eq $false -and
                  $result.owner_instantiated -eq $false -and
                  $result.forbidden_calls.Count -eq 0
    $correctOwner = $ownerFile -eq $expectedOwners[$route]
    $routes[$route] = @{
        owner_file = $ownerFile
        owner_sha256 = $result.owner_sha256
        expected_owner = $expectedOwners[$route]
        owner_matches_a01 = $result.owner_matches_a01
        expected_a01_owner_sha256 = $result.expected_a01_owner_sha256
        recorded_a01_owner_sha256 = $result.recorded_a01_owner_sha256
        source_identity_matches_manifest = $actualOwnerHashMatches
        reached_guarded_boundary = $atBoundary
        forbidden_calls = $result.forbidden_calls
    }
    Add-Check ($route + '_stdout_matches_result') $stdoutMatches $route
    Add-Check ($route + '_stderr_empty') $stderrEmpty $route
    Add-Check ($route + '_selected_owner_hash_matches_manifest') $actualOwnerHashMatches $ownerFile
    Add-Check ($route + '_reached_guarded_boundary_without_side_effects') $atBoundary $route
    Add-Check ($route + '_selected_expected_owner') $correctOwner @{ observed = $ownerFile; expected = $expectedOwners[$route] }
}

$a01Path = 'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py'
$rawPath = 'research/live_control/input_owner_v12.py'
$a01Hash = $manifest.files[$a01Path].sha256
$rawHash = $manifest.files[$rawPath].sha256
$v15PerkeyMismatch = $routes['v15-perkey'].owner_sha256 -eq $rawHash -and
                     $routes['v15-perkey'].owner_sha256 -ne $a01Hash -and
                     $routes['v15-perkey'].owner_matches_a01 -eq $false
Add-Check 'v15_perkey_raw_owner_mismatch_is_exactly_classified' $v15PerkeyMismatch @{ a01 = $a01Hash; raw = $rawHash; observed = $routes['v15-perkey'].owner_sha256 }

$run01 = Join-Path $package 'results/current-head-4158-run01'
$stopText = Get-Content (Join-Path $run01 'v12-perkey.stderr.txt') -Raw
$stopStatus = Get-Content (Join-Path $run01 'run-status.json') -Raw | ConvertFrom-Json -AsHashtable
$stopPreserved = $stopText.Contains("No module named 'openpyxl'") -and
                 $stopStatus.Count -eq 1 -and $stopStatus[0].exit_code -ne 0
Add-Check 'first_environment_stop_preserved' $stopPreserved $stopStatus

$featureGatePass = $routes['v15-perkey'].owner_file -eq $a01Path -and
                   $routes['v15-perkey'].owner_sha256 -eq $a01Hash
$result = @{
    schema = 'v15-perkey-owner-revalidation-audit-v1'
    audit_integrity_pass = ($failures.Count -eq 0)
    feature_gate_pass = $featureGatePass
    disposition = if ($featureGatePass) { 'PASS_STARTUP_OWNER_IDENTITY' } else { 'FAIL_V15_PERKEY_SELECTED_OWNER_IDENTITY' }
    source_count = $manifest.files.Count
    candidate_head = $manifest.ref
    routes = $routes
    checks = $checks.ToArray()
    failures = $failures.ToArray()
    interpretation_limit = 'Startup class identity only; no InputOwner was instantiated and no DOWN/UP, X/OS release, application effect, live threat, or task outcome was observed.'
}
$target = Join-Path $package 'AUDIT.json'
$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $target -Encoding utf8NoBOM
Write-Output ($result | ConvertTo-Json -Depth 12 -Compress)
if ($failures.Count -gt 0) { exit 1 }

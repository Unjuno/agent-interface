$ErrorActionPreference = 'Stop'
$package = $PSScriptRoot
$manifest = Get-Content (Join-Path $package 'source-manifest.json') -Raw | ConvertFrom-Json -AsHashtable
$run = Join-Path $package 'results/current-head-4158-run02'
$candidateAudit = Get-Content (Join-Path $package 'AUDIT_REPAIR_01.json') -Raw | ConvertFrom-Json -AsHashtable
$materializedAudit = Get-Content (Join-Path $package 'MATERIALIZED_SOURCE_AUDIT.json') -Raw | ConvertFrom-Json -AsHashtable
$checks = [System.Collections.Generic.List[object]]::new()

function Check([string]$Name, [bool]$Pass, $Details = $null) {
    $checks.Add(@{ name = $Name; pass = $Pass; details = $Details })
}
function Normalize([string]$Value) { $Value.Replace('\', '/') }

$snapshotBad = [System.Collections.Generic.List[string]]::new()
foreach ($entry in $manifest.files.GetEnumerator()) {
    $path = Join-Path $package ("source-snapshots/" + $entry.Key + '.txt')
    if (-not (Test-Path -LiteralPath $path) -or
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value.sha256 -or
        (Get-Item -LiteralPath $path).Length -ne $entry.Value.bytes) {
        $snapshotBad.Add([string]$entry.Key)
    }
}
Check 'all_frozen_source_snapshots_retained' ($snapshotBad.Count -eq 0 -and $manifest.files.Count -eq 56) $snapshotBad.ToArray()

$materialized = $materializedAudit.all_runs_match -eq $true -and
                $materializedAudit.source_count -eq 56 -and
                $materializedAudit.checks.Count -eq 2 -and
                @($materializedAudit.checks | Where-Object { -not $_.pass }).Count -eq 0
Check 'pre_prune_materialized_source_readback_retained' $materialized $materializedAudit.all_runs_match

$runStatus = @(Get-Content (Join-Path $run 'run-status.json') -Raw | ConvertFrom-Json -AsHashtable)
$routeNames = @('v12-perkey','v15-default','v15-perkey')
$routesOk = $runStatus.Count -eq 3 -and @($runStatus | Where-Object { $_.exit_code -ne 0 }).Count -eq 0
$results = @{}
foreach ($route in $routeNames) {
    $resultPath = Join-Path (Join-Path $run $route) 'result.json'
    $stdoutPath = Join-Path $run ($route + '.stdout.txt')
    $stderrPath = Join-Path $run ($route + '.stderr.txt')
    $result = Get-Content $resultPath -Raw | ConvertFrom-Json -AsHashtable
    $stdout = Get-Content $stdoutPath -Raw | ConvertFrom-Json -AsHashtable
    $results[$route] = $result
    $routesOk = $routesOk -and $result.route -eq $route -and
                $result.source_selection_finished -eq $true -and
                $result.session_started -eq $false -and
                $result.owner_instantiated -eq $false -and
                $result.forbidden_calls.Count -eq 0 -and
                $stdout.owner_sha256 -eq $result.owner_sha256 -and
                $stdout.owner_file -eq $result.owner_file -and
                (Get-Item -LiteralPath $stderrPath).Length -eq 0
}
Check 'three_retained_routes_match_no_side_effect_boundary' $routesOk $routeNames

$a01 = 'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py'
$raw = 'research/live_control/input_owner_v12.py'
$v12 = $results['v12-perkey']
$v15 = $results['v15-perkey']
$identityFail = (Normalize $v12.owner_file) -eq $a01 -and
                $v12.owner_sha256 -eq $manifest.files[$a01].sha256 -and
                (Normalize $v15.owner_file) -eq $raw -and
                $v15.owner_sha256 -eq $manifest.files[$raw].sha256 -and
                $v15.owner_sha256 -ne $manifest.files[$a01].sha256
Check 'v15_perkey_identity_failure_reproduced' $identityFail @{ v12_owner=$v12.owner_file; v15_owner=$v15.owner_file }

$candidateAuditValid = $candidateAudit.audit_integrity_pass -eq $true -and
                       $candidateAudit.feature_gate_pass -eq $false -and
                       $candidateAudit.disposition -eq 'FAIL_V15_PERKEY_SELECTED_OWNER_IDENTITY'
Check 'independent_feature_audit_retained' $candidateAuditValid $candidateAudit.disposition

$result = @{
    schema = 'v15-perkey-retained-package-audit-v1'
    source_ref = $manifest.ref
    checks = $checks.ToArray()
    integrity_pass = (@($checks | Where-Object { -not $_.pass }).Count -eq 0)
    feature_disposition = $candidateAudit.disposition
    scope = 'Readback of retained A02 evidence after pruning only verified duplicate materialized copies; no candidate rerun.'
}
$target = Join-Path $package 'RETAINED_PACKAGE_AUDIT.json'
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $target -Encoding utf8NoBOM
$result | ConvertTo-Json -Depth 10 -Compress
if (-not $result.integrity_pass) { exit 1 }

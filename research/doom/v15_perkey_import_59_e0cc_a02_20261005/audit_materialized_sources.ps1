$ErrorActionPreference = 'Stop'
$package = $PSScriptRoot
$manifest = Get-Content (Join-Path $package 'source-manifest.json') -Raw | ConvertFrom-Json -AsHashtable
$runs = @(
    'results/current-head-4158-run01/source',
    'results/current-head-4158-run02/source'
)
$checks = [System.Collections.Generic.List[object]]::new()
foreach ($run in $runs) {
    $root = Join-Path $package $run
    $bad = [System.Collections.Generic.List[string]]::new()
    foreach ($entry in $manifest.files.GetEnumerator()) {
        $relative = [string]$entry.Key
        $expected = $entry.Value
        $path = Join-Path $root $relative
        if (-not (Test-Path -LiteralPath $path) -or
            (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected.sha256 -or
            (Get-Item -LiteralPath $path).Length -ne $expected.bytes) {
            $bad.Add($relative)
        }
    }
    $checks.Add(@{ run = $run; count = $manifest.files.Count; pass = ($bad.Count -eq 0); mismatches = $bad.ToArray() })
}
$result = @{
    schema = 'v15-perkey-materialized-source-readback-v1'
    source_ref = $manifest.ref
    source_count = $manifest.files.Count
    all_runs_match = (($checks | Where-Object { -not $_.pass }).Count -eq 0)
    checks = $checks.ToArray()
    interpretation = 'Read-only byte comparison of replay-materialized source copies against the retained frozen source manifest. No candidate or session was run.'
}
$result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $package 'MATERIALIZED_SOURCE_AUDIT.json') -Encoding utf8NoBOM
$result | ConvertTo-Json -Depth 8 -Compress
if (-not $result.all_runs_match) { exit 1 }

$ErrorActionPreference = 'Stop'
$root = 'C:\Users\junny\Documents\Codex\2026-10-04\agent-interface-native-suite-a01\experiment'
$source = Join-Path $root 'source'
$out = Join-Path $root 'output'
$expected = @{
    source_commit = '25700c9f68e9937fc1057a5da91d14c3971bb2b6'
    runner_blob = 'd70fa82b1b29c4a384a95348697431ec3d28d2a0'
    dockerfile_blob = 'f1464e51c2cc4e493c439f93fc049ccfe6221590'
    requirements_blob = 'c2bd62fb8e00ef32764d35e46276536648b8aea5'
}
$meta = @(Get-Content -LiteralPath (Join-Path $root 'source-files.json') -Raw | ConvertFrom-Json)
$bad = [System.Collections.Generic.List[string]]::new()
foreach ($item in $meta) {
    $path = Join-Path $source $item.path
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $bad.Add("missing:$($item.path)"); continue }
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $header = [System.Text.Encoding]::ASCII.GetBytes("blob $($bytes.Length)`0")
    $payload = [byte[]]::new($header.Length + $bytes.Length)
    [Array]::Copy($header, 0, $payload, 0, $header.Length)
    [Array]::Copy($bytes, 0, $payload, $header.Length, $bytes.Length)
    $actual = [Convert]::ToHexString([System.Security.Cryptography.SHA1]::HashData($payload)).ToLowerInvariant()
    if ($actual -ne $item.sha) { $bad.Add("blob-mismatch:$($item.path)") }
}
$runner = git -C (Split-Path $root -Parent) hash-object (Join-Path $source 'runtime/integration_checks/native.py')
$dockerfile = git -C (Split-Path $root -Parent) hash-object (Join-Path $source 'runtime/integration_checks/Dockerfile')
$buildLog = Get-Content -LiteralPath (Join-Path $out 'build.log') -Raw
$exitReceipt = Get-Content -LiteralPath (Join-Path $out 'build-exit.json') -Raw | ConvertFrom-Json
$command = Get-Content -LiteralPath (Join-Path $out 'build-command.json') -Raw | ConvertFrom-Json
$remoteRequirement = Get-Content -LiteralPath (Join-Path $root 'remote-requirement.json') -Raw | ConvertFrom-Json
$requiredInput = 'research/live_control/requirements-native-mcp.txt'
$requiredLocal = Test-Path -LiteralPath (Join-Path $source $requiredInput) -PathType Leaf
$actualFileCount = @(Get-ChildItem -LiteralPath $source -Recurse -File).Count
$logExplainsMissingInput = $buildLog.Contains($requiredInput) -and $buildLog.Contains('not found') -and $buildLog.Contains('failed to solve')
$checks = [ordered]@{
    frozen_source_commit = ($command.source_commit -eq $expected.source_commit)
    source_manifest_all_git_blobs_match = ($bad.Count -eq 0)
    native_runner_blob = ($runner -eq $expected.runner_blob)
    dockerfile_blob = ($dockerfile -eq $expected.dockerfile_blob)
    requirements_exists_at_frozen_remote_sha = ($remoteRequirement.path -eq $requiredInput -and $remoteRequirement.sha -eq $expected.requirements_blob -and $remoteRequirement.size -eq 12)
    requirements_absent_from_materialized_context = (-not $requiredLocal)
    source_tree_has_no_unmanifested_files = ($actualFileCount -eq $meta.Count)
    build_log_identifies_missing_copy_input = $logExplainsMissingInput
    build_exit_is_nonzero = ($exitReceipt.exit_code -eq 1)
    image_id_not_emitted = (-not (Test-Path -LiteralPath (Join-Path $out 'image-id.txt')))
    candidate_not_run = (-not (Test-Path -LiteralPath (Join-Path $out 'candidate')))
}
$hashes = @()
foreach ($name in @('build-command.json', 'build.log', 'build-exit.json', 'source-files.json')) {
    $p = Join-Path $out $name
    if ($name -eq 'source-files.json') { $p = Join-Path $root $name }
    $hashes += [pscustomobject]@{ path = $name; sha256 = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$result = [ordered]@{
    audit = 'independent-saved-build-stop-audit-v1'
    allocation = '3352-native-suite-wslc-a01-20261004'
    disposition = 'STOP_SETUP'
    checks = $checks
    source_file_count = $meta.Count
    actual_source_file_count = $actualFileCount
    materialized_source_bytes = ($meta | Measure-Object -Property size -Sum).Sum
    source_hash_errors = @($bad)
    remote_requirements_blob = $expected.requirements_blob
    raw_artifacts = $hashes
    candidate_or_test_result = $false
}
$result | ConvertTo-Json -Depth 8

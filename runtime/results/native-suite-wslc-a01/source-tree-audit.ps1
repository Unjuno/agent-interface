param(
    [string]$SourceCommit = '25700c9f68e9937fc1057a5da91d14c3971bb2b6',
    [string]$PackageRoot = $PSScriptRoot
)
$ErrorActionPreference = 'Stop'
$manifestPath = Join-Path $PackageRoot 'source-files.json.gz'
$outputDir = Join-Path $PackageRoot 'output'
[IO.Directory]::CreateDirectory($outputDir) | Out-Null

function Get-GhJson([string]$Endpoint) {
    $raw = gh api $Endpoint
    if ($LASTEXITCODE -ne 0) { throw "gh api failed: $Endpoint" }
    return $raw | ConvertFrom-Json
}

$compressed = [IO.File]::OpenRead($manifestPath)
$memory = [IO.MemoryStream]::new()
try {
    $gzip = [IO.Compression.GZipStream]::new($compressed, [IO.Compression.CompressionMode]::Decompress)
    try { $gzip.CopyTo($memory) } finally { $gzip.Dispose() }
} finally { $compressed.Dispose() }
$manifest = @([Text.Encoding]::UTF8.GetString($memory.ToArray()) | ConvertFrom-Json)
$manifestByPath = @{}
foreach ($item in $manifest) { $manifestByPath[$item.path] = $item }

$workflow = Get-GhJson "repos/Unjuno/agent-interface/contents/.github/workflows/native-mcp-v1.yml?ref=$SourceCommit"
$runtimeDirs = @(
    'runtime/cli_v1', 'runtime/host_v1', 'runtime/motor_state_v1',
    'runtime/selector_v1', 'runtime/core_v1', 'runtime/backends',
    'runtime/integration_checks', 'runtime/distribution_v2', 'runtime/guarded_x11_v1'
)
$expected = [System.Collections.Generic.List[object]]::new()
foreach ($directory in $runtimeDirs) {
    $parent = Split-Path $directory -Parent
    $name = Split-Path $directory -Leaf
    $children = Get-GhJson "repos/Unjuno/agent-interface/contents/$parent`?ref=$SourceCommit"
    $treeSha = ($children | Where-Object name -eq $name | Select-Object -First 1).sha
    if (-not $treeSha) { throw "Cannot resolve tree: $directory" }
    $tree = Get-GhJson "repos/Unjuno/agent-interface/git/trees/$treeSha`?recursive=1"
    if ($tree.truncated) { throw "Truncated Git tree: $directory" }
    foreach ($entry in $tree.tree | Where-Object type -eq 'blob') {
        $expected.Add([pscustomobject]@{ path = "$directory/$($entry.path)"; sha = $entry.sha; size = $entry.size })
    }
}

$runtimeRoot = Get-GhJson "repos/Unjuno/agent-interface/contents/runtime`?ref=$SourceCommit"
foreach ($entry in $runtimeRoot | Where-Object { $_.type -eq 'file' -and $_.name -eq '__init__.py' }) {
    $expected.Add([pscustomobject]@{ path = $entry.path; sha = $entry.sha; size = $entry.size })
}
$researchRoot = Get-GhJson "repos/Unjuno/agent-interface/contents/research`?ref=$SourceCommit"
$liveTreeSha = ($researchRoot | Where-Object name -eq 'live_control' | Select-Object -First 1).sha
$liveTree = Get-GhJson "repos/Unjuno/agent-interface/git/trees/$liveTreeSha"
if ($liveTree.truncated) { throw 'Truncated direct research/live_control Git tree' }
$liveFiles = @($liveTree.tree | Where-Object type -eq 'blob')
foreach ($entry in $liveFiles) {
    $expected.Add([pscustomobject]@{ path = "research/live_control/$($entry.path)"; sha = $entry.sha; size = $entry.size })
}

$expected = @($expected | Sort-Object path -Unique)
$missing = @($expected | Where-Object { -not $manifestByPath.ContainsKey($_.path) })
$mismatched = @($expected | Where-Object { $manifestByPath.ContainsKey($_.path) -and $manifestByPath[$_.path].sha -ne $_.sha })
$expectedPaths = @{}; foreach ($item in $expected) { $expectedPaths[$item.path] = $true }
$extra = @($manifest | Where-Object { -not $expectedPaths.ContainsKey($_.path) })
$contentsListing = Get-GhJson "repos/Unjuno/agent-interface/contents/research/live_control`?ref=$SourceCommit"
$contentsFiles = @($contentsListing | Where-Object type -eq 'file').Count

$result = [ordered]@{
    audit = 'independent-frozen-source-tree-completeness-v1'
    ref = $SourceCommit
    workflow_blob = $workflow.sha
    research_live_control_tree = $liveTreeSha
    research_direct_tree_truncated = $liveTree.truncated
    research_direct_tree_files = $liveFiles.Count
    contents_endpoint_files_returned = $contentsFiles
    expected_selected_file_count = $expected.Count
    materialized_manifest_file_count = $manifest.Count
    matched_file_count = ($expected.Count - $missing.Count - $mismatched.Count)
    missing_file_count = $missing.Count
    blob_mismatch_count = $mismatched.Count
    extra_file_count = $extra.Count
    requirements_missing = ($missing.path -contains 'research/live_control/requirements-native-mcp.txt')
    result = 'INCOMPLETE_SOURCE_CONTEXT'
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outputDir 'source-tree-audit.json') -Encoding utf8
$missing | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outputDir 'source-tree-missing.json') -Encoding utf8
$result | ConvertTo-Json -Depth 5

param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$Image = "python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
)
$ErrorActionPreference = "Stop"
$source = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$freeze = Get-Content -LiteralPath (Join-Path $source "FREEZE.json") -Raw | ConvertFrom-Json
if ($freeze.status -ne "AUTHORIZED" -or -not $freeze.resource_assignment_record) {
    throw "No explicit #5085 assignment for this exact allocation; no container invocation started."
}
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $source "..\..\..")).Path
git -C $repoRoot fetch origin main --quiet
if ($LASTEXITCODE -ne 0) { throw "Could not refresh origin/main; no container invocation started." }
$currentMain = (git -C $repoRoot rev-parse origin/main).Trim()
if ($currentMain -ne $freeze.planning_main) { throw "main drift: expected $($freeze.planning_main), observed $currentMain; no invocation started." }
git -C $repoRoot merge-base --is-ancestor $freeze.planning_main HEAD
if ($LASTEXITCODE -ne 0) { throw "Frozen main is not an ancestor of this checkout; no invocation started." }
foreach ($entry in $freeze.source_sha256.PSObject.Properties) {
    $path = Join-Path $source $entry.Name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing frozen source: $($entry.Name)" }
    $observed = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    if ($observed -ne $entry.Value) { throw "Frozen source changed: $($entry.Name)" }
}
$imageListing = (& wslc.exe images 2>&1 | Out-String)
if ($imageListing -notmatch [regex]::Escape(($freeze.wslc_image_config_id -replace "^sha256:", "").Substring(0, 12))) {
    throw "Pinned image is not present locally; pulls are forbidden by this freeze."
}
$out = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $out) { throw "Output path already exists; no invocation started: $out" }
New-Item -ItemType Directory -Path $out | Out-Null
$candidateLog = Join-Path $out "candidate.stdout.txt"
$candidateErr = Join-Path $out "candidate.stderr.txt"
$candidateArgs = @("run", "--rm", "--pull", "never", "--network", "none", "--cpus", "1", "--memory", "512M",
    "--volume", "${source}:/src:ro", "--volume", "${out}:/out:rw", $Image,
    "python3", "-B", "/src/candidate.py", "/out/candidate")
& wslc.exe @candidateArgs 1> $candidateLog 2> $candidateErr
$candidateExit = $LASTEXITCODE
Set-Content -LiteralPath (Join-Path $out "candidate.exit.txt") -Value $candidateExit -NoNewline
if ($candidateExit -ne 0) { exit $candidateExit }
$auditLog = Join-Path $out "audit.stdout.txt"
$auditErr = Join-Path $out "audit.stderr.txt"
$auditArgs = @("run", "--rm", "--pull", "never", "--network", "none", "--cpus", "1", "--memory", "512M",
    "--volume", "${source}:/src:ro", "--volume", "${out}:/out:rw", $Image,
    "python3", "-B", "/src/audit.py", "/out/candidate")
& wslc.exe @auditArgs 1> $auditLog 2> $auditErr
$auditExit = $LASTEXITCODE
Set-Content -LiteralPath (Join-Path $out "audit.exit.txt") -Value $auditExit -NoNewline
exit $auditExit

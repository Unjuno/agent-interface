$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$results = Join-Path $root 'results'
New-Item -ItemType Directory -Path $results -Force | Out-Null
$marker = Join-Path $results 'candidate.started.json'
if (Test-Path -LiteralPath $marker) {
    throw 'The one-shot candidate start marker already exists; refusing to rerun.'
}

$frozen = Get-Content -Raw -LiteralPath (Join-Path $root 'FROZEN.json') | ConvertFrom-Json
$python = (Get-Command python).Source
if ($python -ine $frozen.python.path) { throw 'Python path differs from FROZEN.json.' }
if ((& $python --version) -ne $frozen.python.version) { throw 'Python version differs from FROZEN.json.' }
if ((Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash.ToLower() -ne $frozen.python.sha256) {
    throw 'Python executable hash differs from FROZEN.json.'
}
$codex = (Get-Command codex.exe).Source
if ($codex -ine $frozen.codex_executable) { throw 'Codex executable path differs from FROZEN.json.' }
if ((Get-FileHash -LiteralPath $codex -Algorithm SHA256).Hash.ToLower() -ne $frozen.codex_sha256) {
    throw 'Codex executable hash differs from FROZEN.json.'
}
$repoRoot = (Resolve-Path (Join-Path $root '..\..\..')).Path
$head = (& git -C $repoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot identify the frozen source checkout.' }
& git -C $repoRoot merge-base --is-ancestor $frozen.base_commit $head
if ($LASTEXITCODE -ne 0) { throw 'HEAD is not descended from the frozen base commit.' }
$dirty = @(& git -C $repoRoot status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) { throw 'Tracked source tree is dirty; refusing formal run.' }
foreach ($entry in $frozen.source_sha256.PSObject.Properties) {
    $relative = $entry.Name
    $path = Join-Path $root $relative
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $entry.Value) {
        throw "Frozen source hash mismatch: $relative"
    }
}
foreach ($entry in $frozen.fixture_sha256.PSObject.Properties) {
    $relative = $entry.Name
    $path = Join-Path $root $relative
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $entry.Value) {
        throw "Frozen fixture hash mismatch: $relative"
    }
}
foreach ($entry in $frozen.environment_preflight_sha256.PSObject.Properties) {
    $relative = $entry.Name
    $path = Join-Path $root $relative
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $entry.Value) {
        throw "Frozen environment evidence hash mismatch: $relative"
    }
}
if ((Get-FileHash -LiteralPath (Join-Path $root 'environment\runtime-selection.txt') -Algorithm SHA256).Hash.ToLower() -ne $frozen.runtime_selection_sha256) {
    throw 'Frozen runtime-selection evidence hash mismatch.'
}

$stdout = Join-Path $results 'candidate.stdout.json'
$stderr = Join-Path $results 'candidate.stderr.txt'
$exitPath = Join-Path $results 'candidate.exit'
$commandPath = Join-Path $results 'candidate.command.json'
foreach ($outputPath in @($stdout, $stderr, $exitPath, $commandPath)) {
    if (Test-Path -LiteralPath $outputPath) { throw "Candidate output already exists: $outputPath" }
}

$runId = [Guid]::NewGuid().ToString()
$started = [DateTimeOffset]::UtcNow.ToString('o')
$argv = @('-B', 'probe.py', '--frame-201', 'fixtures/synthetic-seq201.png',
          '--frame-202', 'fixtures/synthetic-seq202.png')
$runRecord = [ordered]@{
    run_id = $runId
    started_utc = $started
    candidate_runs = 1
    retries = 0
    base_commit = $frozen.base_commit
    source_checkout_head = $head
    python_executable = $python
    python_version = $frozen.python.version
    python_sha256 = $frozen.python.sha256
    codex_executable = $codex
    codex_sha256 = $frozen.codex_sha256
    working_directory = $root
    command = 'python ' + ($argv -join ' ')
    argv = $argv
}
$utf8 = [System.Text.UTF8Encoding]::new($false)
$markerHandle = [System.IO.File]::Open($marker, [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
try {
    $markerBytes = $utf8.GetBytes(($runRecord | ConvertTo-Json -Depth 5) + "`n")
    $markerHandle.Write($markerBytes, 0, $markerBytes.Length)
} finally {
    $markerHandle.Dispose()
}
[System.IO.File]::WriteAllText($commandPath, ($runRecord | ConvertTo-Json -Depth 5) + "`n", $utf8)

$processInfo = [System.Diagnostics.ProcessStartInfo]::new()
$processInfo.FileName = $python
$processInfo.Arguments = ($argv | ForEach-Object { '"' + $_ + '"' }) -join ' '
$processInfo.WorkingDirectory = $root
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
$processInfo.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)
$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $processInfo
try {
    if (-not $process.Start()) { throw 'Could not start the frozen Python candidate.' }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $candidateExit = $process.ExitCode
    $stdoutText = $stdoutTask.GetAwaiter().GetResult()
    $stderrText = $stderrTask.GetAwaiter().GetResult()
} catch {
    $stdoutText = if ($stdoutTask) { $stdoutTask.GetAwaiter().GetResult() } else { '' }
    $stderrText = if ($stderrTask) { $stderrTask.GetAwaiter().GetResult() } else { $_.ToString() }
    [System.IO.File]::WriteAllText($stdout, $stdoutText, $utf8)
    [System.IO.File]::WriteAllText($stderr, $stderrText, $utf8)
    throw
} finally {
    $process.Dispose()
}
[System.IO.File]::WriteAllText($stdout, $stdoutText, $utf8)
[System.IO.File]::WriteAllText($stderr, $stderrText, $utf8)
[System.IO.File]::WriteAllText($exitPath, [string]$candidateExit + "`n", $utf8)
$runRecord['ended_utc'] = [DateTimeOffset]::UtcNow.ToString('o')
$runRecord['exit_code'] = $candidateExit
[System.IO.File]::WriteAllText($marker, ($runRecord | ConvertTo-Json -Depth 5) + "`n", $utf8)
exit $candidateExit

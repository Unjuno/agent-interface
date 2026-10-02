param(
    [Parameter(Mandatory = $true)][string]$LeaseRecord,
    [Parameter(Mandatory = $true)][string]$LeaseStartUtc,
    [Parameter(Mandatory = $true)][string]$LeaseEndUtc
)

$ErrorActionPreference = 'Stop'
$Allocation = 'GPU-MEMORY-SHARING-4972-20261002-10'
$Image = 'pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067'
$Wslc = 'C:\Program Files\WSL\wslc.exe'
$Source = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$OutputRoot = Join-Path $Source 'formal-attempt-01'

if ($LeaseRecord -notmatch '^https://github\.com/Unjuno/agent-interface/issues/5085#issuecomment-\d+$') {
    throw 'STOP: supply the exact coordinator lease comment URL from Issue #5085.'
}
$start = [DateTimeOffset]::Parse($LeaseStartUtc).ToUniversalTime()
$end = [DateTimeOffset]::Parse($LeaseEndUtc).ToUniversalTime()
$now = [DateTimeOffset]::UtcNow
if ($end -le $start -or $now -lt $start -or $now -ge $end) {
    throw 'STOP: current UTC time is outside the exact coordinator-assigned interval.'
}
if (-not (Test-Path -LiteralPath $Wslc -PathType Leaf)) { throw 'STOP: wslc.exe unavailable.' }
if (Test-Path -LiteralPath $OutputRoot) { throw 'STOP: formal output path already exists.' }

$freezePath = Join-Path $Source 'FREEZE.json'
$freeze = Get-Content -LiteralPath $freezePath -Raw | ConvertFrom-Json
if ($freeze.allocation -ne $Allocation -or $freeze.runtime.image -ne $Image) { throw 'STOP: freeze identity mismatch.' }
foreach ($name in @('construction_check.py', 'runner.py', 'audit.py', 'test_audit.py')) {
    $expected = $freeze.source_sha256.$name
    $actual = (Get-FileHash -LiteralPath (Join-Path $Source $name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "STOP: frozen source hash mismatch for $name." }
}
$expectedScript = $freeze.source_sha256.'run_formal.ps1'
$actualScript = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualScript -ne $expectedScript) { throw 'STOP: frozen formal-runner script hash mismatch.' }

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $Source '..\..\..')).Path
$mainLine = & git -C $repoRoot ls-remote origin refs/heads/main
if ($LASTEXITCODE -ne 0) { throw 'STOP: unable to read current origin/main.' }
$currentMain = (($mainLine -split '\s+')[0]).Trim()
if ($currentMain -ne $freeze.base_main) { throw "STOP: main advanced; refreeze required ($currentMain)." }

$info = (& $Wslc info 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0 -or $info -notmatch 'wslc 3\.0\.1\.0') { throw 'STOP: expected WSLc runtime version not verified.' }
$inventory = @(& $Wslc list --all 2>&1 | Where-Object { $_.ToString().Trim() -ne '' })
if ($LASTEXITCODE -ne 0 -or $inventory.Count -ne 1) { throw 'STOP: WSLc inventory is not known empty.' }
$imageInfoText = (& $Wslc inspect $Image 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'STOP: pinned image inspection failed.' }
$imageInfo = @($imageInfoText | ConvertFrom-Json)[0]
if ($imageInfo.Id -ne $freeze.runtime.image_id -or $imageInfo.Os -ne 'linux' -or $imageInfo.Architecture -ne 'amd64' -or $imageInfo.RepoDigests -notcontains $Image) {
    throw 'STOP: cached image ID/digest/platform mismatch.'
}

$gpuLine = (& nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu --format=csv,noheader,nounits 2>&1 | Select-Object -First 1)
if ($LASTEXITCODE -ne 0) { throw 'STOP: host GPU inventory query failed.' }
$gpuFields = @($gpuLine -split ',' | ForEach-Object { $_.Trim() })
if ($gpuFields.Count -ne 4 -or $gpuFields[0] -ne 'NVIDIA GeForce RTX 3080 Laptop GPU' -or [int]$gpuFields[1] -lt 16384 -or [int]$gpuFields[2] -lt 10240) {
    throw 'STOP: expected RTX 3080 or >=10 GiB initial free VRAM not verified.'
}
$drive = Get-PSDrive -Name ([IO.Path]::GetPathRoot($OutputRoot).TrimEnd('\').TrimEnd(':')) -ErrorAction SilentlyContinue
if ($null -eq $drive -or $drive.Free -lt 1GB) { throw 'STOP: insufficient/unknown host free space.' }

# Process/owner collision review is a required human gate; this helper never
# stops, kills, or alters another process, container, image, volume, or distro.
New-Item -ItemType Directory -Path $OutputRoot | Out-Null
$candidateOut = Join-Path $OutputRoot 'candidate'
$auditOut = Join-Path $OutputRoot 'audit'
$constructionOut = Join-Path $OutputRoot 'construction'
New-Item -ItemType Directory -Path $candidateOut, $auditOut, $constructionOut | Out-Null
$inventory | Set-Content -LiteralPath (Join-Path $OutputRoot 'containers_before.txt') -Encoding Ascii
$info | Set-Content -LiteralPath (Join-Path $OutputRoot 'wslc_info.txt') -Encoding Ascii
$imageInfoText | Set-Content -LiteralPath (Join-Path $OutputRoot 'image_inspect.json') -Encoding Ascii
$gpuLine | Set-Content -LiteralPath (Join-Path $OutputRoot 'gpu_before.csv') -Encoding Ascii
$currentMain | Set-Content -LiteralPath (Join-Path $OutputRoot 'current_main.txt') -Encoding Ascii
@{
    allocation = $Allocation
    lease_record = $LeaseRecord
    lease_start_utc = $start.ToString('o')
    lease_end_utc = $end.ToString('o')
    invocation_utc = $now.ToString('o')
    gpu_query = $gpuLine
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputRoot 'gate.json') -Encoding Ascii

$constructionArgs = @(
    'run', '--rm', '--pull', 'never', '--network', 'none', '--cpus', '1', '--memory', '1G',
    '--user', '65534:65534', '--mount', "type=bind,source=$Source,target=/src,readonly",
    '--mount', "type=bind,source=$constructionOut,target=/construction",
    '--env', 'PYTHONDONTWRITEBYTECODE=1', $Image, 'python', '/src/construction_check.py',
    '/construction/write_probe.txt'
)
$constructionArgs | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $OutputRoot 'construction_argv.json') -Encoding Ascii
& $Wslc @constructionArgs 1> (Join-Path $OutputRoot 'construction.stdout.txt') 2> (Join-Path $OutputRoot 'construction.stderr.txt')
$constructionExit = $LASTEXITCODE
Set-Content -LiteralPath (Join-Path $OutputRoot 'construction.exit') -Value $constructionExit -Encoding Ascii
if ($constructionExit -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $constructionOut 'write_probe.txt'))) {
    throw 'STOP: WSLc construction suite or unprivileged output-bind probe failed; candidate not launched.'
}
$postConstructionInventory = @(& $Wslc list --all 2>&1 | Where-Object { $_.ToString().Trim() -ne '' })
$postConstructionInventory | Set-Content -LiteralPath (Join-Path $OutputRoot 'containers_after_construction.txt') -Encoding Ascii
if ($LASTEXITCODE -ne 0 -or $postConstructionInventory.Count -ne 1) {
    throw 'STOP: WSLc inventory not empty after construction --rm container; candidate not launched.'
}

$samplesPath = Join-Path $OutputRoot 'host_gpu_samples.csv'
$samplerError = Join-Path $OutputRoot 'host_sampler.stderr.txt'
$stdout = Join-Path $OutputRoot 'candidate.stdout.txt'
$stderr = Join-Path $OutputRoot 'candidate.stderr.txt'
$header = 'timestamp,utilization_gpu_pct,memory_used_mib,memory_free_mib'
Set-Content -LiteralPath $samplesPath -Value $header -Encoding Ascii
Set-Content -LiteralPath $samplerError -Value '' -Encoding Ascii

$samplerJob = Start-Job -Name "gpu-a10-host-sampler-$PID" -ArgumentList $samplesPath, $samplerError -ScriptBlock {
    param($CsvPath, $ErrorPath)
    while ($true) {
        try {
            $row = & nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,memory.free --format=csv,noheader,nounits 2>&1
            if ($LASTEXITCODE -ne 0) { throw ($row | Out-String) }
            Add-Content -LiteralPath $CsvPath -Value $row -Encoding Ascii
        } catch {
            Add-Content -LiteralPath $ErrorPath -Value ($_ | Out-String) -Encoding Ascii
            break
        }
        Start-Sleep -Seconds 1
    }
}

$candidateExit = 125
$auditExit = 125
try {
    $deadline = [DateTimeOffset]::UtcNow.AddSeconds(12)
    do {
        Start-Sleep -Milliseconds 250
        $sampleRows = @(Import-Csv -LiteralPath $samplesPath)
        if ($samplerJob.State -ne 'Running' -and $sampleRows.Count -eq 0) { throw 'STOP: host GPU sampler exited before a baseline sample.' }
    } while ($sampleRows.Count -eq 0 -and [DateTimeOffset]::UtcNow -lt $deadline)
    if ($sampleRows.Count -eq 0 -or [double]$sampleRows[0].memory_free_mib -lt 10240) { throw 'STOP: host sampler baseline absent or below 10 GiB.' }

    $sourceMount = "type=bind,source=$Source,target=/src,readonly"
    $sampleMount = "type=bind,source=$samplesPath,target=/samples/host_gpu_samples.csv,readonly"
    $candidateMount = "type=bind,source=$candidateOut,target=/out"
    $candidateArgs = @(
        'run', '--rm', '--pull', 'never', '--network', 'none', '--gpus', 'all',
        '--cpus', '6', '--memory', '8G', '--user', '65534:65534',
        '--mount', $sourceMount, '--mount', $sampleMount, '--mount', $candidateMount,
        '--env', 'GPU_A10_OUTPUT=/out', $Image, 'python', '/src/runner.py', '/samples/host_gpu_samples.csv'
    )
    $candidateArgs | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $OutputRoot 'candidate_argv.json') -Encoding Ascii
    & $Wslc @candidateArgs 1> $stdout 2> $stderr
    $candidateExit = $LASTEXITCODE
    Set-Content -LiteralPath (Join-Path $OutputRoot 'candidate.exit') -Value $candidateExit -Encoding Ascii
} finally {
    if ($samplerJob.State -eq 'Running') { Stop-Job -Job $samplerJob }
    Wait-Job -Job $samplerJob -Timeout 5 | Out-Null
    Receive-Job -Job $samplerJob 2>&1 | Out-Null
    Remove-Job -Job $samplerJob -Force -ErrorAction SilentlyContinue
}

if ($candidateExit -eq 0) {
    $postCandidateInventory = @(& $Wslc list --all 2>&1 | Where-Object { $_.ToString().Trim() -ne '' })
    $postCandidateInventory | Set-Content -LiteralPath (Join-Path $OutputRoot 'containers_after_candidate.txt') -Encoding Ascii
    if ($LASTEXITCODE -ne 0 -or $postCandidateInventory.Count -ne 1) {
        Set-Content -LiteralPath (Join-Path $OutputRoot 'audit.exit') -Value 'SKIPPED_POST_CANDIDATE_CONTAINER_INVENTORY_UNKNOWN' -Encoding Ascii
        throw 'HOLD: WSLc inventory is not empty after --rm candidate; no auditor container launched.'
    }
    $auditArgs = @(
        'run', '--rm', '--pull', 'never', '--network', 'none', '--cpus', '1', '--memory', '1G',
        '--user', '65534:65534', '--mount', $sourceMount,
        '--mount', "type=bind,source=$candidateOut,target=/candidate,readonly",
        '--mount', $sampleMount, '--mount', "type=bind,source=$auditOut,target=/audit",
        $Image, 'python', '/src/audit.py', '/candidate/candidate.jsonl',
        '/candidate/candidate_summary.json', '/samples/host_gpu_samples.csv', '/audit/audit.json'
    )
    $auditArgs | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $OutputRoot 'audit_argv.json') -Encoding Ascii
    & $Wslc @auditArgs 1> (Join-Path $OutputRoot 'audit.stdout.txt') 2> (Join-Path $OutputRoot 'audit.stderr.txt')
    $auditExit = $LASTEXITCODE
    Set-Content -LiteralPath (Join-Path $OutputRoot 'audit.exit') -Value $auditExit -Encoding Ascii
    $postAuditInventory = @(& $Wslc list --all 2>&1 | Where-Object { $_.ToString().Trim() -ne '' })
    $postAuditInventory | Set-Content -LiteralPath (Join-Path $OutputRoot 'containers_after_audit.txt') -Encoding Ascii
} else {
    Set-Content -LiteralPath (Join-Path $OutputRoot 'audit.exit') -Value 'SKIPPED_CANDIDATE_NONZERO' -Encoding Ascii
}

Write-Output "allocation=$Allocation candidate_exit=$candidateExit audit_exit=$auditExit"
if ($candidateExit -ne 0) { exit $candidateExit }
exit $auditExit

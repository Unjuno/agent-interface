$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = (Resolve-Path (Join-Path $Here '..\..\..')).Path
$Bundle = Join-Path $Repo 'research\issue_3676_audit_hardening_v1'
$Evidence = Join-Path $Here 'results\formal01'
$Image = 'sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
if (Test-Path $Evidence) { throw 'Formal output already exists; refusing to overwrite or rerun.' }
$m = Get-Content (Join-Path $Here 'SOURCE_MANIFEST.json') -Raw | ConvertFrom-Json
if ((git -C $Repo rev-parse HEAD).Trim() -ne $m.validation_base) { throw 'Validation base mismatch.' }
if ((docker --context desktop-linux version --format '{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}') -ne '28.5.1 linux/amd64') { throw 'Docker Desktop engine mismatch.' }
if ((docker --context desktop-linux image inspect $Image --format '{{.Id}} {{.Os}}/{{.Architecture}}') -ne "$Image linux/amd64") { throw 'Pinned image mismatch.' }
foreach ($entry in $m.files) {
    $actual = (Get-FileHash (Join-Path $Bundle $entry.path) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $entry.sha256) { throw "Frozen source mismatch: $($entry.path)" }
}
New-Item -ItemType Directory -Path $Evidence | Out-Null
$src = ($Bundle -replace '\\','/')
$out = ($Evidence -replace '\\','/')
docker --context desktop-linux run --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=512m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,source=$src,target=/work,readonly" --workdir /work $Image python -B -m unittest -v test_audit.py *> (Join-Path $Evidence 'tests.log')
$testExit = $LASTEXITCODE
Set-Content (Join-Path $Evidence 'tests.exit') $testExit -Encoding ascii
if ($testExit -ne 0) { throw "Test container failed ($testExit); preserve output and do not start container 2 or rerun." }
docker --context desktop-linux run --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=512m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,source=$src,target=/work,readonly" --mount "type=bind,source=$out,target=/out" --workdir /work $Image python -B audit.py evidence/raw.json --freeze evidence/predecessor_FREEZE.json --study-freeze evidence/FREEZE.json --output /out/hardening_audit.json *> (Join-Path $Evidence 'cli.log')
$cliExit = $LASTEXITCODE
Set-Content (Join-Path $Evidence 'cli.exit') $cliExit -Encoding ascii
if ($cliExit -ne 0) { throw "CLI container failed ($cliExit); preserve output and do not rerun." }
$resultBytes = [IO.File]::ReadAllBytes((Join-Path $Evidence 'hardening_audit.json'))
$baselineBytes = [IO.File]::ReadAllBytes((Join-Path $Bundle 'evidence\hardening_audit.json'))
$resultHash = (Get-FileHash (Join-Path $Evidence 'hardening_audit.json') -Algorithm SHA256).Hash.ToLowerInvariant()
$parsed = [Text.Encoding]::UTF8.GetString($resultBytes) | ConvertFrom-Json
if ($resultHash -ne 'e2ac7b32c1da563cbcd3cbea285ac5ace4f98d43b3cb9ea046d2bf6c1adbbbc0') { throw 'CLI output digest differs from frozen baseline.' }
if (-not [Linq.Enumerable]::SequenceEqual([byte[]]$resultBytes, [byte[]]$baselineBytes)) { throw 'CLI output is not byte-identical to retained baseline.' }
if ($parsed.status -ne 'PASS_OFFLINE_STRUCTURAL_AUDIT' -or $parsed.errors.Count -ne 0 -or $parsed.corruption_controls_rejected.Count -ne 21 -or @($parsed.corruption_controls_rejected.Values | Where-Object { $_ -ne $true }).Count -ne 0) { throw 'Independent output assertions failed.' }
$summary = [ordered]@{ allocation='issue-3690-dockerdesktop-host-01'; decision='PASS_DOCKERDESKTOP_HOST_VALIDATION_SCOPED'; docker='28.5.1 linux/amd64'; image_id=$Image; source_commit=$m.target_source_commit; test_container_exit=$testExit; test_count=5; cli_container_exit=$cliExit; cli_status=$parsed.status; errors=@($parsed.errors).Count; corruption_controls_rejected=$parsed.corruption_controls_rejected.Count; cli_sha256=$resultHash; byte_identical_to_retained=$true; xres_formal=0; input=0; model=0; network=0 }
$summary | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $Evidence 'RESULT.json') -Encoding utf8
Get-ChildItem $Evidence -File | Where-Object Name -ne 'SHA256SUMS' | Get-FileHash -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLowerInvariant())  $($_.Path.Substring($Evidence.Length + 1).Replace('\','/'))" } | Set-Content (Join-Path $Evidence 'SHA256SUMS') -Encoding ascii
Write-Output ($summary | ConvertTo-Json -Compress -Depth 5)

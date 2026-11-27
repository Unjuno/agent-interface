$ErrorActionPreference = 'Stop'
$packet = $PSScriptRoot
$repo = [IO.Path]::GetFullPath((Join-Path $packet '..\..\..'))
$out = Join-Path $packet 'output'
$deps = Join-Path $repo 'research\integration\wslc_standard_caller_xvfb_20261025_r09\deps'
$stage = Join-Path $repo 'research\integration\wslc_standard_caller_xvfb_20261025_r16\stage'
$xkb = Join-Path $repo 'research\integration\wslc_standard_caller_xvfb_20261025_r34\xkb-materialized'
$meta = Get-Content (Join-Path $packet 'INVOCATION-METADATA.json') -Raw | ConvertFrom-Json
$image = $meta.image
$name = $meta.container_name
New-Item -ItemType Directory -Force -Path $out | Out-Null
foreach ($path in @($repo, $deps, $stage, $xkb, $out)) {
    if (-not (Test-Path -LiteralPath $path -PathType Container)) { throw "required mount missing: $path" }
}
$existing = & docker.exe ps -a --filter "name=^$name$" --format '{{.Names}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker container inventory failed' }
if ($existing -contains $name) { throw "unique container name already exists: $name" }
$inspect = & docker.exe image inspect --format '{{.RepoDigests}}' $image 2>&1
if ($LASTEXITCODE -ne 0 -or ($inspect -join "`n") -notmatch 'a2d43bffc46670d7108bb3c0468c67c5557c4c92e83e1e34cbff1322ad1b94dc') { throw 'pinned image is not locally available with the expected digest' }
$inspect | Set-Content -Encoding utf8 (Join-Path $out 'pinned-image-inspect.txt')
$args = @(
    'run', '--name', $name, '--network', 'none', '--cpus', '2', '--memory', '2g', '--pids-limit', '128',
    '--tmpfs', '/tmp:rw,exec,nosuid,nodev,mode=1777,size=512m',
    '--mount', "type=bind,source=$repo,target=/repo,readonly",
    '--mount', "type=bind,source=$deps,target=/deps,readonly",
    '--mount', "type=bind,source=$stage,target=/stage,readonly",
    '--mount', "type=bind,source=$xkb,target=/xkb,readonly",
    '--mount', "type=bind,source=$out,target=/out",
    $image, '/bin/bash', "/repo/research/integration/wslc_standard_caller_xvfb_20261025_r46/container-init.sh"
)
& docker.exe @args *> (Join-Path $out 'docker-run-raw.log')
$runCode = $LASTEXITCODE
$runCode | Set-Content -Encoding ascii (Join-Path $out 'docker-run-exit-code.txt')
& docker.exe inspect --format '{{.State.Status}} {{.State.ExitCode}} {{.HostConfig.NetworkMode}} {{.HostConfig.Memory}} {{.HostConfig.NanoCpus}} {{.HostConfig.PidsLimit}} {{json .HostConfig.Tmpfs}}' $name *> (Join-Path $out 'container-state-before-cleanup.txt')
$inspectCode = $LASTEXITCODE
$inspectCode | Set-Content -Encoding ascii (Join-Path $out 'container-inspect-before-cleanup-exit-code.txt')
& docker.exe inspect --format '{{range .Mounts}}{{.Destination}}:readonly={{if .RW}}false{{else}}true{{end}}{{println}}{{end}}' $name *> (Join-Path $out 'container-mounts-before-cleanup.txt')
& docker.exe logs $name *> (Join-Path $out 'container-logs.log')
& docker.exe rm --force $name *> (Join-Path $out 'docker-cleanup.log')
$cleanupCode = $LASTEXITCODE
$cleanupCode | Set-Content -Encoding ascii (Join-Path $out 'docker-cleanup-exit-code.txt')
& docker.exe inspect $name 2>&1 *> (Join-Path $out 'container-inspect-after-cleanup.txt')
$afterCode = $LASTEXITCODE
$afterCode | Set-Content -Encoding ascii (Join-Path $out 'container-inspect-after-cleanup-exit-code.txt')
if ($afterCode -ne 0) { 'container absent after exact-name cleanup' | Set-Content -Encoding utf8 (Join-Path $out 'container-absent-after-cleanup.txt') }
if ($inspectCode -ne 0 -or $cleanupCode -ne 0 -or $afterCode -eq 0) { throw 'container inspection or exact-name cleanup did not complete as expected' }
exit $runCode

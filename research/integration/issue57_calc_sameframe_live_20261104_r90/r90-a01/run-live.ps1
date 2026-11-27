$ErrorActionPreference = 'Stop'
$attempt = 'D:\ai57-main-current-20261104\research\integration\issue57_calc_sameframe_live_20261104_r90\r90-a01'
$repo = 'D:\ai57-main-current-20261104'
$stdoutPath = Join-Path $attempt 'docker-host.stdout.txt'
$cidPath = Join-Path $attempt 'container.cid'
$started = [DateTime]::UtcNow.ToString('o')
$dockerArgs = @(
  'run','--rm','--pull=never','--name','ai57-issue57-r90-a01-live','--network','bridge',
  '--cidfile',$cidPath,'--memory','4g','--memory-swap','4g','--cpus','2','--pids-limit','256',
  '--log-driver','local','--env','ATTEMPT_DIR=r90-a01',
  '--mount','type=bind,source=D:/ai57-main-current-20261104,target=/workspace,readonly',
  '--mount','type=bind,source=D:/ai57-main-current-20261104/research/integration/issue57_calc_sameframe_live_20261104_r90,target=/evidence',
  '--workdir','/workspace','sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425',
  'bash','/evidence/r90-a01/runner.sh')
& docker @dockerArgs *> $stdoutPath
$dockerExit = $LASTEXITCODE
$ended = [DateTime]::UtcNow.ToString('o')
$containerId = if (Test-Path -LiteralPath $cidPath) { (Get-Content -LiteralPath $cidPath -Raw).Trim() } else { $null }
$record = [ordered]@{schema='agent-interface/docker-run-exit-v1';attempt_id='issue57-r90-a01';container_name='ai57-issue57-r90-a01-live';container_id=$containerId;image_id='sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425';started_utc=$started;ended_utc=$ended;exit_code=[int]$dockerExit;captured_from='PowerShell $LASTEXITCODE immediately after docker run'}
$record | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $attempt 'docker-exit-code.json') -Encoding utf8
Write-Output "docker_exit_code=$dockerExit"
if ($dockerExit -ne 0) { exit $dockerExit }


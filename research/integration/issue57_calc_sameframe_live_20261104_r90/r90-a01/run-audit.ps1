$ErrorActionPreference = 'Stop'
$attempt = 'D:\ai57-main-current-20261104\research\integration\issue57_calc_sameframe_live_20261104_r90\r90-a01'
$repo = 'D:\ai57-main-current-20261104'
$stdoutPath = Join-Path $attempt 'audit-host.stdout.txt'
$dockerArgs = @(
  'run','--rm','--pull=never','--name','ai57-issue57-r90-a01-audit','--network','none',
  '--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=32m','--cpus','1','--memory','512m','--pids-limit','64',
  '--cap-drop','ALL','--security-opt','no-new-privileges',
  '--mount','type=bind,source=D:/ai57-main-current-20261104,target=/workspace,readonly',
  '--mount','type=bind,source=D:/ai57-main-current-20261104/research/integration/issue57_calc_sameframe_live_20261104_r90/r90-a01,target=/evidence/r90-a01',
  '--workdir','/workspace','sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425',
  'python3','/evidence/r90-a01/audit.py')
& docker @dockerArgs *> $stdoutPath
$auditExit = $LASTEXITCODE
$record = [ordered]@{schema='agent-interface/docker-audit-exit-v1';attempt_id='issue57-r90-a01';exit_code=[int]$auditExit;captured_from='PowerShell $LASTEXITCODE immediately after offline audit container'}
$record | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $attempt 'audit-exit-code.json') -Encoding utf8
Write-Output "audit_exit_code=$auditExit"


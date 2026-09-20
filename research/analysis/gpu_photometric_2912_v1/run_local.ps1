$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$resultRoot = Join-Path $PSScriptRoot 'results\alloc-20260921-01'
if (Test-Path -LiteralPath $resultRoot) {
    if (Get-ChildItem -LiteralPath $resultRoot -Force | Select-Object -First 1) {
        throw "Allocation output already exists; refusing to rerun: $resultRoot"
    }
} else {
    New-Item -ItemType Directory -Path $resultRoot | Out-Null
}

$env:CUBLAS_WORKSPACE_CONFIG = ':4096:8'
$env:REPO_ROOT = $repo
$env:RESULT_ROOT = $resultRoot
try {
    & python (Join-Path $PSScriptRoot 'train_eval.py') *> (Join-Path $resultRoot 'runner.log')
    $runExit = $LASTEXITCODE
    if ($runExit -ne 0) {
        throw "STOP_TRAIN_RUNNER_EXIT_$runExit; preserve runner.log and do not retry"
    }
    & python (Join-Path $PSScriptRoot 'audit.py') $repo `
        (Join-Path $resultRoot 'results.json') `
        (Join-Path $resultRoot 'audit.json') *> (Join-Path $resultRoot 'audit.log')
    $auditExit = $LASTEXITCODE
    if ($auditExit -ne 0) {
        throw "STOP_INDEPENDENT_AUDIT_EXIT_$auditExit; preserve all artifacts and do not rerun"
    }
} finally {
    Remove-Item Env:CUBLAS_WORKSPACE_CONFIG -ErrorAction SilentlyContinue
    Remove-Item Env:REPO_ROOT -ErrorAction SilentlyContinue
    Remove-Item Env:RESULT_ROOT -ErrorAction SilentlyContinue
}

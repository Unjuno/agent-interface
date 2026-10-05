$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$results = Join-Path $PSScriptRoot 'results'
New-Item -ItemType Directory -Path $results -Force | Out-Null

$cases = @(
    @{ Name = 'planner-adapter'; Directory = '.'; Command = @('-m', 'unittest', 'research.live_control.test_persistent_planner_adapter_v2', '-v') },
    @{ Name = 'app-server-client'; Directory = 'research/live_control'; Command = @('test_app_server_utf8.py', '-v') },
    @{ Name = 'v39-paired-signal'; Directory = 'research/doom'; Command = @('test_map01_overlap_controller_v39_dual_signal.py', '-v') },
    @{ Name = 'v39-controller'; Directory = 'research/doom'; Command = @('test_map01_overlap_controller_v39.py', '-v') },
    @{ Name = 'v39-wait'; Directory = 'research/doom'; Command = @('test_overlap_controller_v39_wait.py', '-v') },
    @{ Name = 'v39-pair-dispatch'; Directory = 'research/doom'; Command = @('test_map01_v39_pair_wait_dispatch.py', '-v') }
)

$failed = $false
foreach ($case in $cases) {
    $workingDirectory = if ($case.Directory -eq '.') { $repo } else { Join-Path $repo $case.Directory }
    $log = Join-Path $results ($case.Name + '.txt')
    $command = $case.Command
    Push-Location $workingDirectory
    try {
        & python @command *> $log
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    Set-Content -LiteralPath ($log + '.exit') -Value ([string]$exitCode) -Encoding ascii
    if ($exitCode -ne 0) { $failed = $true }
}

Push-Location $repo
try {
    $compileLog = Join-Path $results 'py-compile.txt'
    & python -m py_compile research/live_control/codex_app_server_client_v2.py research/live_control/persistent_planner_adapter_v2.py research/doom/map01_overlap_controller_v39.py *> $compileLog
    $compileExit = $LASTEXITCODE
}
finally {
    Pop-Location
}
Set-Content -LiteralPath (Join-Path $results 'py-compile.txt.exit') -Value ([string]$compileExit) -Encoding ascii
if ($compileExit -ne 0) { $failed = $true }
if ($failed) { exit 1 }
exit 0

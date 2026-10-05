# unittest writes progress to stderr; PowerShell's Stop preference can turn
# successful native stderr output into a terminating error before exit checks.
$ErrorActionPreference = 'Continue'

function Write-Utf8Lf([string]$Path, [string]$Text) {
    $normalized = $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    [System.IO.File]::WriteAllText(
        $Path, $normalized, [System.Text.UTF8Encoding]::new($false))
}

function Normalize-NativeLog([string]$Path) {
    $text = [System.IO.File]::ReadAllText($Path)
    Write-Utf8Lf $Path $text
}

function Invoke-Python([string[]]$Arguments, [string]$WorkingDirectory,
                       [string]$LogPath) {
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = 'python'
    $quotedArguments = foreach ($argument in $Arguments) {
        '"' + $argument.Replace('"', '\"') + '"'
    }
    $startInfo.Arguments = $quotedArguments -join ' '
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $startInfo.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)
    $startInfo.EnvironmentVariables['PYTHONUTF8'] = '1'

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    Write-Utf8Lf $LogPath ($stdout.Result + $stderr.Result)
    return $process.ExitCode
}
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
    $exitCode = Invoke-Python $case.Command $workingDirectory $log
    Write-Utf8Lf ($log + '.exit') ([string]$exitCode + "`n")
    if ($exitCode -ne 0) { $failed = $true }
}

$compileLog = Join-Path $results 'py-compile.txt'
$compileExit = Invoke-Python @('-m', 'py_compile',
    'research/live_control/codex_app_server_client_v2.py',
    'research/live_control/persistent_planner_adapter_v2.py',
    'research/doom/map01_overlap_controller_v39.py') $repo $compileLog
Normalize-NativeLog $compileLog
Write-Utf8Lf (Join-Path $results 'py-compile.txt.exit') ([string]$compileExit + "`n")
if ($compileExit -ne 0) { $failed = $true }
if ($failed) { exit 1 }
exit 0

function ConvertTo-WslcWindowsArgument {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Argument)

    if ($Argument.Length -gt 0 -and $Argument -notmatch '[\s"]') {
        return $Argument
    }

    $builder = [System.Text.StringBuilder]::new()
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($character in $Argument.ToCharArray()) {
        if ($character -eq '\') {
            $backslashes++
            continue
        }
        if ($character -eq '"') {
            [void]$builder.Append(('\' * (2 * $backslashes + 1)))
            [void]$builder.Append('"')
            $backslashes = 0
            continue
        }
        if ($backslashes -gt 0) {
            [void]$builder.Append(('\' * $backslashes))
            $backslashes = 0
        }
        [void]$builder.Append($character)
    }
    if ($backslashes -gt 0) {
        [void]$builder.Append(('\' * (2 * $backslashes)))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Invoke-WslcBoundedProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][AllowEmptyCollection()][string[]]$ArgumentList,
        [Parameter(Mandatory)][ValidateRange(1, 3600)][int]$TimeoutSeconds,
        [System.Text.Encoding]$OutputEncoding
    )

    $quotedArguments = foreach ($argument in $ArgumentList) {
        ConvertTo-WslcWindowsArgument -Argument $argument
    }
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FilePath
    $startInfo.Arguments = $quotedArguments -join ' '
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    if ($null -ne $OutputEncoding) {
        $startInfo.StandardOutputEncoding = $OutputEncoding
        $startInfo.StandardErrorEncoding = $OutputEncoding
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            throw "Could not start child process: $FilePath"
        }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $timedOut = -not $process.WaitForExit($TimeoutSeconds * 1000)
        if ($timedOut) {
            # This stops only the CLI process we started. It does not establish
            # that a WSLc server-side operation or container was cancelled.
            try {
                $process.Kill()
                if (-not $process.WaitForExit(2000)) {
                    throw "Child process $($process.Id) did not exit within 2s after Kill()."
                }
            }
            catch {
                if (-not $process.HasExited) {
                    throw "Timed out and could not retire child process $($process.Id): $_"
                }
            }
        }
        else {
            # Drain both redirected pipes before reading ExitCode.
            $process.WaitForExit()
        }
        if (-not $stdoutTask.Wait(2000) -or -not $stderrTask.Wait(2000)) {
            throw "Child process output pipes did not close within 2s (pid=$($process.Id))."
        }
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        [pscustomobject]@{
            FilePath = $FilePath
            ProcessId = $process.Id
            TimedOut = $timedOut
            ExitCode = if ($timedOut) { $null } else { $process.ExitCode }
            StandardOutput = $stdout
            StandardError = $stderr
        }
    }
    finally {
        $process.Dispose()
    }
}

Export-ModuleMember -Function Invoke-WslcBoundedProcess

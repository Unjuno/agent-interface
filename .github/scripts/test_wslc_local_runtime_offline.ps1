$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'wslc_bounded_process.psm1') -Force

$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$fakeRoot = Join-Path $tempRoot "wslc-offline-fake-$([guid]::NewGuid().ToString('N'))"
[void](New-Item -ItemType Directory -Path $fakeRoot)
$fakeSource = @'
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading;

public static class FakeWslcCli
{
    public static int Main()
    {
        string name = Process.GetCurrentProcess().ProcessName.ToLowerInvariant();
        string[] args = Environment.GetCommandLineArgs().Skip(1).ToArray();
        if (name == "wsl")
        {
            Console.WriteLine("Fake WSL version");
            return 0;
        }
        if (args.Length > 0 && args[0] == "version")
        {
            Console.WriteLine("Fake WSLc version");
            return 0;
        }
        if (args.Length >= 3 && args[0] == "container" && args[1] == "list")
        {
            string cleanupMode = Environment.GetEnvironmentVariable("FAKE_WSLC_MODE") ?? "success";
            if (cleanupMode == "cleanup-timeout")
            {
                string root = Environment.GetEnvironmentVariable("FAKE_WSLC_TEST_ROOT");
                File.WriteAllText(Path.Combine(root, "cleanup.pid"), Process.GetCurrentProcess().Id.ToString());
                Thread.Sleep(30000);
            }
            if (cleanupMode == "cleanup-nonempty")
            {
                Console.WriteLine("[{\"id\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\"}]");
                return 0;
            }
            Console.WriteLine("[]");
            return 0;
        }
        if (args.Length == 0 || args[0] != "run") return 41;

        int cidIndex = Array.IndexOf(args, "--cidfile");
        if (cidIndex < 0 || cidIndex + 1 >= args.Length) return 42;
        string cidPath = args[cidIndex + 1];
        File.WriteAllText(cidPath, new string('a', 64));
        File.WriteAllText(cidPath + ".pid", Process.GetCurrentProcess().Id.ToString());

        int volumeIndex = Array.IndexOf(args, "--volume");
        if (volumeIndex < 0 || volumeIndex + 1 >= args.Length) return 43;
        string volume = args[volumeIndex + 1];
        const string marker = ":/probe:ro";
        int markerIndex = volume.IndexOf(marker, StringComparison.OrdinalIgnoreCase);
        if (markerIndex < 0) return 44;
        string hostPath = volume.Substring(0, markerIndex);
        if (File.ReadAllText(Path.Combine(hostPath, "sentinel.bin")) != "wslc-readonly-probe") return 45;

        string mode = Environment.GetEnvironmentVariable("FAKE_WSLC_MODE") ?? "success";
        if (mode == "timeout") Thread.Sleep(30000);
        if (mode == "failure")
        {
            Console.Error.WriteLine("fake run failure after cid receipt");
            return 12;
        }
        return 0;
    }
}
'@

$oldPath = $env:PATH
$oldMode = $env:FAKE_WSLC_MODE
$oldFakeRoot = $env:FAKE_WSLC_TEST_ROOT
$probePathsBefore = @(
    Get-ChildItem -LiteralPath $tempRoot -Directory -Filter 'agent-interface-wslc-probe-*' -ErrorAction SilentlyContinue |
        ForEach-Object { $_.FullName })
try {
    $fakeBase = Join-Path $fakeRoot 'fake-cli.exe'
    Add-Type -TypeDefinition $fakeSource -OutputAssembly $fakeBase `
        -OutputType ConsoleApplication -ErrorAction Stop
    Copy-Item -LiteralPath $fakeBase -Destination (Join-Path $fakeRoot 'wsl.exe')
    Copy-Item -LiteralPath $fakeBase -Destination (Join-Path $fakeRoot 'wslc.exe')
    $env:PATH = $fakeRoot + ';' + $oldPath
    $env:FAKE_WSLC_TEST_ROOT = $fakeRoot
    $powershell = (Get-Command powershell.exe -ErrorAction Stop).Source
    $smokeScript = Join-Path $PSScriptRoot 'test_wslc_local_runtime.ps1'

    $env:FAKE_WSLC_MODE = 'success'
    $success = Invoke-WslcBoundedProcess -FilePath $powershell -TimeoutSeconds 20 `
        -ArgumentList @('-NoProfile', '-NonInteractive', '-File', $smokeScript,
            '-RunTimeoutSeconds', '2')
    if ($success.ExitCode -ne 0 -or $success.StandardOutput -notmatch 'WSLc local runtime probe: PASS') {
        throw "Offline success path failed: $($success | ConvertTo-Json -Compress)"
    }
    $probePathsAfterSuccess = @(
        Get-ChildItem -LiteralPath $tempRoot -Directory -Filter 'agent-interface-wslc-probe-*' -ErrorAction SilentlyContinue |
            ForEach-Object { $_.FullName })
    if (@($probePathsAfterSuccess | Where-Object { $_ -notin $probePathsBefore }).Count -ne 0) {
        throw 'Offline successful cleanup left a new probe directory.'
    }

    foreach ($mode in @('failure', 'timeout', 'cleanup-timeout', 'cleanup-nonempty')) {
        $env:FAKE_WSLC_MODE = $mode
        $runLimit = if ($mode -eq 'timeout') { '1' } else { '2' }
        $cleanupLimit = if ($mode -eq 'cleanup-timeout') { '1' } else { '2' }
        $outcome = Invoke-WslcBoundedProcess -FilePath $powershell -TimeoutSeconds 20 `
            -ArgumentList @('-NoProfile', '-NonInteractive', '-File', $smokeScript,
                '-RunTimeoutSeconds', $runLimit, '-CleanupTimeoutSeconds', $cleanupLimit)
        if ($outcome.ExitCode -eq 0) {
            throw "Expected offline $mode failure, but smoke succeeded."
        }
        if ($mode -in @('timeout', 'cleanup-timeout') -and
                (($outcome.StandardOutput + $outcome.StandardError) -notmatch 'Timed out after 1s')) {
            throw "Timed-out run was not reported: $($outcome | ConvertTo-Json -Compress)"
        }
        $combined = $outcome.StandardOutput + $outcome.StandardError
        $match = [regex]::Match($combined, 'Preserved receipts and logs at (?<path>[^;]+);')
        if (-not $match.Success) {
            throw "Unconfirmed $mode outcome did not report retained evidence: $combined"
        }
        $preserved = [System.IO.Path]::GetFullPath($match.Groups['path'].Value.Trim())
        if (-not $preserved.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to inspect path outside temp root: $preserved"
        }
        $cidPath = Join-Path $preserved 'container.cid'
        if (-not (Test-Path -LiteralPath $cidPath -PathType Leaf) -or
                (Get-Content -LiteralPath $cidPath -Raw).Trim() -notmatch '^[0-9a-f]{64}$') {
            throw "Unconfirmed $mode outcome lost its container receipt."
        }
        if (-not (Test-Path -LiteralPath (Join-Path $preserved 'wslc-run.stderr.txt'))) {
            throw "Unconfirmed $mode outcome lost its raw CLI log."
        }
        if ($mode -eq 'cleanup-timeout') {
            $fakePid = [int](Get-Content -LiteralPath (Join-Path $fakeRoot 'cleanup.pid') -Raw)
        }
        else {
            $fakePid = [int](Get-Content -LiteralPath ($cidPath + '.pid') -Raw)
        }
        if ($mode -in @('timeout', 'cleanup-timeout') -and
                (Get-Process -Id $fakePid -ErrorAction SilentlyContinue)) {
            throw "Offline $mode CLI process $fakePid was not retired."
        }
        if ($mode -in @('cleanup-timeout', 'cleanup-nonempty') -and
                -not (Test-Path -LiteralPath (Join-Path $preserved 'wslc-cleanup-query.stdout.txt'))) {
            throw "Unconfirmed $mode outcome lost its scoped cleanup output file."
        }
        # The fake executable cannot create a real container. Remove only this
        # test's GUID-owned directory after its receipt/log assertions pass.
        Remove-Item -LiteralPath $preserved -Recurse -Force
    }

    Write-Output 'Offline WSLc smoke harness: PASS (success cleanup, failed-run retention, run/cleanup timeouts, non-empty cleanup retention)'
}
finally {
    $env:PATH = $oldPath
    if ($null -eq $oldMode) { Remove-Item Env:FAKE_WSLC_MODE -ErrorAction SilentlyContinue }
    else { $env:FAKE_WSLC_MODE = $oldMode }
    if ($null -eq $oldFakeRoot) { Remove-Item Env:FAKE_WSLC_TEST_ROOT -ErrorAction SilentlyContinue }
    else { $env:FAKE_WSLC_TEST_ROOT = $oldFakeRoot }
    if (Test-Path -LiteralPath $fakeRoot) {
        Remove-Item -LiteralPath $fakeRoot -Recurse -Force
    }
}

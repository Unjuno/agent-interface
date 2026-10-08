$ErrorActionPreference = 'Stop'

$wslc = Get-Command wslc.exe -ErrorAction SilentlyContinue
if (-not $wslc) {
    throw 'wslc.exe is required. Update WSL to 2.9.3 or later, then reopen PowerShell.'
}
$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $wsl) {
    throw 'wsl.exe is required to record the WSL runtime version.'
}

Write-Output 'WSL version:'
& $wsl.Source --version
if ($LASTEXITCODE -ne 0) {
    throw "Could not read WSL version (exit code $LASTEXITCODE)."
}
Write-Output 'WSLc version:'
& $wslc.Source version
if ($LASTEXITCODE -ne 0) {
    throw "Could not read WSLc version (exit code $LASTEXITCODE)."
}

$image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$probePath = [System.IO.Path]::GetFullPath((Join-Path $tempRoot "agent-interface-wslc-probe-$([guid]::NewGuid().ToString('N'))"))
if (-not $probePath.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing to create a probe directory outside the system temporary directory.'
}

$containerName = "agent-interface-wslc-probe-$([guid]::NewGuid().ToString('N'))"
$sentinelPath = Join-Path $probePath 'sentinel.bin'
$probeCode = @'
import errno
from pathlib import Path

sentinel = Path("/probe/sentinel.bin")
if sentinel.read_bytes() != b"wslc-readonly-probe":
    raise SystemExit("mounted source bytes differ")
try:
    sentinel.write_bytes(b"must-not-write")
except OSError as error:
    if error.errno != errno.EROFS:
        raise
    print("read-only bind mount: PASS (EROFS)")
else:
    raise SystemExit("read-only bind mount unexpectedly allowed a write")
'@

try {
    [void](New-Item -ItemType Directory -Path $probePath)
    [System.IO.File]::WriteAllBytes($sentinelPath, [System.Text.Encoding]::UTF8.GetBytes('wslc-readonly-probe'))

    & $wslc.Source run --rm --name $containerName --pull never --network none --memory 512M --cpus 1 `
        --volume "${probePath}:/probe:ro" $image python -B -c $probeCode
    if ($LASTEXITCODE -ne 0) {
        throw "WSLc probe failed with exit code $LASTEXITCODE. Preserve the output above for diagnosis."
    }

    $containers = & $wslc.Source container list --all
    if ($LASTEXITCODE -ne 0) {
        throw "Could not verify WSLc cleanup (exit code $LASTEXITCODE)."
    }
    if (($containers -join "`n") -match [regex]::Escape($containerName)) {
        throw "The --rm probe container remains after completion: $containerName"
    }

    Write-Output 'WSLc local runtime probe: PASS'
    Write-Output "Image: $image"
    Write-Output 'Network: none; memory: 512M; CPUs: 1; source mount: read-only; cleanup: verified'
    Write-Output 'Note: WSL may report that swap/cgroup memory limits are unavailable; this probe does not test swap isolation or peak-memory enforcement.'
}
finally {
    if (Test-Path -LiteralPath $probePath) {
        Remove-Item -LiteralPath $probePath -Recurse -Force
    }
}

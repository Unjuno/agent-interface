param(
    [ValidateRange(100, 30000)][int]$ConnectTimeoutMs = 2000,
    [ValidateRange(100, 30000)][int]$ResponseTimeoutMs = 5000
)

# Read-only probe of Docker Desktop's Linux engine. Never starts/retries input,
# restarts services, or launches a Docker CLI process that can remain pending.
$ErrorActionPreference = 'Stop'
$probeClock = [System.Diagnostics.Stopwatch]::StartNew()
$probeResult = [ordered]@{
    schema = 'agent-interface/docker-engine-probe-v1'
    endpoint = 'npipe:////./pipe/dockerDesktopLinuxEngine'
    started_at = [DateTimeOffset]::UtcNow.ToString('o')
    status = 'unavailable'
    pipe_connected = $false
    http_status = $null
    input_dispatched = $false
    gui_readiness_verified = $false
}
$probePipe = $null
try {
    $probePipe = [System.IO.Pipes.NamedPipeClientStream]::new(
        '.', 'dockerDesktopLinuxEngine', [System.IO.Pipes.PipeDirection]::InOut,
        [System.IO.Pipes.PipeOptions]::Asynchronous)
    $probePipe.Connect($ConnectTimeoutMs)
    $probeResult.pipe_connected = $true
    $probeRequest = [Text.Encoding]::ASCII.GetBytes(
        "GET /_ping HTTP/1.1`r`nHost: docker`r`nConnection: close`r`n`r`n")
    $probeResponseClock = [Diagnostics.Stopwatch]::StartNew()
    $probeWrite = $probePipe.WriteAsync($probeRequest, 0, $probeRequest.Length)
    if (-not $probeWrite.Wait($ResponseTimeoutMs)) {
        throw [TimeoutException]::new('Ping write exceeded response deadline')
    }
    $probeBuffer = [byte[]]::new(1024)
    $probeHeaders = ''
    while (-not $probeHeaders.Contains("`r`n`r`n")) {
        $probeRemaining = $ResponseTimeoutMs - [int]$probeResponseClock.ElapsedMilliseconds
        if ($probeRemaining -le 0) {
            throw [TimeoutException]::new('Ping response deadline exceeded')
        }
        $probeRead = $probePipe.ReadAsync($probeBuffer, 0, $probeBuffer.Length)
        if (-not $probeRead.Wait($probeRemaining)) {
            throw [TimeoutException]::new('Ping response deadline exceeded')
        }
        if ($probeRead.Result -eq 0) { throw 'Engine closed connection before HTTP headers' }
        $probeHeaders += [Text.Encoding]::ASCII.GetString($probeBuffer, 0, $probeRead.Result)
        if ($probeHeaders.Length -gt 8192) { throw 'Engine response headers exceeded limit' }
    }
    if ($probeHeaders -notmatch '^HTTP/1\.[01] ([0-9]{3}) ') {
        throw 'Engine returned invalid HTTP status line'
    }
    $probeResult.http_status = [int]$Matches[1]
    if ($probeResult.http_status -eq 200) { $probeResult.status = 'api_responsive' }
    else { $probeResult.status = 'http_error' }
} catch {
    $probeResult.error = $_.Exception.Message
    if ($_.Exception -is [TimeoutException]) { $probeResult.status = 'timeout' }
} finally {
    if ($null -ne $probePipe) { $probePipe.Dispose() }
}
$probeResult.elapsed_ms = $probeClock.ElapsedMilliseconds
$probeResult | ConvertTo-Json -Depth 3
if ($probeResult.status -ne 'api_responsive') { exit 1 }

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
"probe_started_utc=$([DateTime]::UtcNow.ToString('o'))"
$roots = @(
  'C:\Users\user\AppData\Roaming\npm\node_modules',
  'C:\Users\user\AppData\Local\Programs\Codex',
  'C:\Users\user\AppData\Local\OpenAI',
  'C:\Program Files\nodejs\node_modules',
  'C:\Program Files\WindowsApps\OpenAI.Codex_26.1117.3838.0_x64__2p2nqsd0c76g0\app'
)
$found = @()
foreach ($root in $roots) {
  if (Test-Path -LiteralPath $root) {
    $found += Get-ChildItem -LiteralPath $root -Recurse -File -Filter codex.js -ErrorAction SilentlyContinue | ForEach-Object FullName
  }
}
if ($found.Count) { $found | ForEach-Object { "WINDOWS_CODEX_JS_FOUND=$_" } } else { 'WINDOWS_CODEX_JS_NOT_FOUND_IN_SCOPED_ROOTS' }
$chrome = @('C:\Program Files\Google\Chrome\Application\chrome.exe','C:\Program Files (x86)\Google\Chrome\Application\chrome.exe','C:\Users\user\AppData\Local\Google\Chrome\Application\chrome.exe') | Where-Object { Test-Path -LiteralPath $_ }
if ($chrome.Count) { $chrome | ForEach-Object { "WINDOWS_CHROME_FOUND=$_" } } else { 'WINDOWS_CHROME_NOT_FOUND_IN_SCOPED_PATHS' }
'wsl_probe:'
wsl.exe -d Ubuntu -- sh -lc 'for c in google-chrome google-chrome-stable chromium chromium-browser; do command -v "$c" 2>/dev/null; done; dpkg-query -W -f="${binary:Package}\n" "*chromium*" 2>/dev/null || true'
if ($LASTEXITCODE -ne 0) { throw "WSL probe exit $LASTEXITCODE" }
"probe_finished_utc=$([DateTime]::UtcNow.ToString('o'))"

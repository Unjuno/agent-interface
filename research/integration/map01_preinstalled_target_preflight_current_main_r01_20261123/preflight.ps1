$ErrorActionPreference = 'Stop'
$paths = @(
    'C:\Program Files\GZDoom\gzdoom.exe',
    'C:\Program Files (x86)\GZDoom\gzdoom.exe',
    'C:\Program Files (x86)\Steam\steamapps\common\GZDoom\gzdoom.exe',
    'C:\Program Files\Steam\steamapps\common\GZDoom\gzdoom.exe',
    'C:\Users\user\Downloads\gzdoom.exe',
    'C:\Users\user\Documents\GZDoom\gzdoom.exe'
)
$candidates = @($paths | ForEach-Object {
    [pscustomobject]@{ path = $_; exists = [bool](Test-Path -LiteralPath $_ -PathType Leaf) }
})
$commands = @(Get-Command gzdoom.exe,gzdoom -ErrorAction SilentlyContinue | ForEach-Object {
    [pscustomobject]@{ name = $_.Name; source = $_.Source }
})
$processes = @(Get-Process -Name gzdoom -ErrorAction SilentlyContinue | ForEach-Object {
    [pscustomobject]@{ id = $_.Id; path = $_.Path }
})
$registry = @(Get-ItemProperty @(
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
) -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match 'GZDoom|Doom' } | ForEach-Object {
    [pscustomobject]@{ display_name = $_.DisplayName; install_location = $_.InstallLocation }
})
[pscustomobject]@{
    generated_at_utc = [DateTime]::UtcNow.ToString('o')
    main_sha = 'e67ca18cd3e8a5ccb0288b41ed2f5d0bb94bc6c7'
    host = [Environment]::OSVersion.VersionString
    action_taken = 'read-only path, process, command, and uninstall-registry inspection; no application launched'
    candidates = $candidates
    commands = $commands
    processes = $processes
    uninstall_registry = $registry
} | ConvertTo-Json -Depth 6

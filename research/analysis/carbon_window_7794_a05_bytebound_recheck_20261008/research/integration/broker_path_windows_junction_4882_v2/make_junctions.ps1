param(
    [Parameter(Mandatory=$true)][string]$Fixture,
    [Parameter(Mandatory=$true)][string]$Repo,
    [Parameter(Mandatory=$true)][string]$Outside
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Junction -Path (Join-Path $Repo 'in-junction') -Target (Join-Path $Repo 'internal') | Out-Null
New-Item -ItemType Junction -Path (Join-Path $Repo 'external-junction') -Target $Outside | Out-Null
$items = @(
    Get-Item -LiteralPath (Join-Path $Repo 'in-junction'),
    Get-Item -LiteralPath (Join-Path $Repo 'external-junction')
)
if ($items.Count -ne 2 -or @($items | Where-Object { $_.LinkType -ne 'Junction' }).Count -ne 0) {
    throw 'junction identity verification failed'
}
Write-Output 'JUNCTION_SETUP_OK'

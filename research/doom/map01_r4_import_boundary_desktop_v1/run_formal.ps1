$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = (Resolve-Path (Join-Path $Here '..\..\..')).Path
$Evidence = Join-Path $Here 'results\formal01'
$Image = 'sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
if (Test-Path $Evidence) { throw 'Formal output already exists; refusing to overwrite or rerun.' }
if ((git -C $Repo rev-parse HEAD).Trim() -ne 'fab3b392fb854696312a85a6b859a78369c3e737') { throw 'Unexpected source base.' }
if ((docker --context desktop-linux version --format '{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}') -ne '28.5.1 linux/amd64') { throw 'Docker Desktop engine mismatch.' }
if ((docker --context desktop-linux image inspect $Image --format '{{.Id}} {{.Os}}/{{.Architecture}}') -ne "$Image linux/amd64") { throw 'Image identity/platform mismatch.' }
$Manifest = Get-Content (Join-Path $Here 'SOURCE_MANIFEST.json') -Raw | ConvertFrom-Json
foreach ($entry in $Manifest.files) {
    $actual = (Get-FileHash (Join-Path $Here $entry.path) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $entry.sha256) { throw "Source hash mismatch: $($entry.path)" }
}
New-Item -ItemType Directory -Path $Evidence | Out-Null
$MountIn = ($Here -replace '\\','/')
$MountOut = ($Evidence -replace '\\','/')
docker --context desktop-linux run --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=256m --pids-limit=32 --cap-drop=ALL --security-opt=no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=16m --mount "type=bind,source=$MountIn,target=/src,readonly" --mount "type=bind,source=$MountOut,target=/evidence" --workdir /src $Image python /src/runner.py
if ($LASTEXITCODE -ne 0) { throw "Formal runner stopped with exit $LASTEXITCODE; preserve this output and do not retry." }
Get-ChildItem $Evidence -File | Get-FileHash -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLowerInvariant())  $($_.Path | Split-Path -Leaf)" } | Set-Content (Join-Path $Evidence 'SHA256SUMS') -Encoding ascii

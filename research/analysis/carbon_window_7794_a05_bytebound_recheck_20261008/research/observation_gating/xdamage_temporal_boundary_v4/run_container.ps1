param(
  [Parameter(Mandatory=$true)][ValidateSet("construction", "formal")][string]$Mode,
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$SourceCommit,
  [ValidateRange(1, 2)][int]$ConstructionSessions = 1
)
$ErrorActionPreference = "Stop"
$Image = "agent-interface-gtk-preflight:local"
$ExpectedImage = "sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4"
$SourceDir = "research/observation_gating/xdamage_temporal_boundary_v4"
$RepoFull = (Resolve-Path -LiteralPath $RepoRoot).Path
git -C $RepoFull cat-file -e "$SourceCommit^{commit}"
if ($LASTEXITCODE -ne 0) { throw "STOP_SOURCE_COMMIT_UNAVAILABLE" }
$FreezeText = git -C $RepoFull show "${SourceCommit}:${SourceDir}/FREEZE.json" | Out-String
if ($LASTEXITCODE -ne 0) { throw "STOP_FREEZE_UNAVAILABLE" }
$Freeze = $FreezeText | ConvertFrom-Json
$ExpectedLauncher = $Freeze.source_sha256.'run_container.ps1'
$ActualLauncher = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ExpectedLauncher -ne $ActualLauncher) { throw "STOP_LAUNCHER_SOURCE_HASH_MISMATCH" }
$Out = [IO.Path]::GetFullPath([string]$Freeze.host_output_paths.$Mode)
if ($Out -cne [string]$Freeze.host_output_paths.$Mode) { throw "STOP_OUTPUT_PATH_NOT_CANONICAL" }
if (Test-Path -LiteralPath $Out) { throw "STOP_OUTPUT_EXISTS $Out" }
$ActualImage = docker image inspect $Image --format "{{.Id}}"
if ($LASTEXITCODE -ne 0 -or $ActualImage.Trim() -ne $ExpectedImage) { throw "STOP_IMAGE_ID_MISMATCH expected=$ExpectedImage actual=$ActualImage" }
$Sessions = if ($Mode -eq "formal") { 8 } else { $ConstructionSessions }
New-Item -ItemType Directory -Path $Out | Out-Null
$Inner = @'
set -eu
mkdir -p /src
cd /repo
for f in run_formal.py xdamage_native.c audit_formal.py exact_gate.py temporal_protocol.py test_temporal_protocol.py run_container.ps1 FREEZE.json; do
  git show "$SOURCE_GIT_COMMIT:research/observation_gating/xdamage_temporal_boundary_v4/$f" > "/src/$f"
done
cd /src
python3 -m unittest -v test_temporal_protocol.py
python3 run_formal.py --mode "$RUN_MODE" --sessions "$RUN_SESSIONS" --out "/results/$RUN_MODE"
python3 audit_formal.py "/results/$RUN_MODE" --source-root /src
'@
docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m --tmpfs /src:rw,nosuid,nodev,noexec,size=64m --cpus 1 --memory 2g --pids-limit 64 --security-opt no-new-privileges --cap-drop ALL -e "SOURCE_GIT_COMMIT=$SourceCommit" -e "RUN_MODE=$Mode" -e "RUN_SESSIONS=$Sessions" -v "${RepoFull}:/repo:ro" -v "${Out}:/results:rw" --entrypoint /bin/sh $Image -ec $Inner
if ($LASTEXITCODE -ne 0) { throw "STOP_DOCKER_EXPERIMENT_EXIT_$LASTEXITCODE" }

param(
  [ValidateSet("construction", "formal")][string]$Mode = "construction",
  [string]$Out = (Join-Path $PSScriptRoot ("results-" + $Mode + "-v3")),
  [ValidateRange(1, 2)][int]$ConstructionSessions = 1
)
$ErrorActionPreference = "Stop"
$Image = "agent-interface-gtk-preflight:local"
$Expected = "sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4"
$Actual = docker image inspect $Image --format "{{.Id}}"
if ($LASTEXITCODE -ne 0 -or $Actual.Trim() -ne $Expected) { throw "STOP_IMAGE_ID_MISMATCH expected=$Expected actual=$Actual" }
if (Test-Path -LiteralPath $Out) { throw "STOP_OUTPUT_EXISTS $Out" }
$RepoRoot = (git -C $PSScriptRoot rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw "STOP_NOT_IN_GIT_REPOSITORY" }
$SourceCommit = (git -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $SourceCommit.Length -ne 40) { throw "STOP_SOURCE_COMMIT_UNAVAILABLE" }
New-Item -ItemType Directory -Path $Out | Out-Null
$OutFull = (Resolve-Path -LiteralPath $Out).Path
$RepoFull = (Resolve-Path -LiteralPath $RepoRoot).Path
$ContainerMode = $Mode
$Sessions = if ($Mode -eq "formal") { 8 } else { $ConstructionSessions }
$Inner = @'
set -eu
mkdir -p /src
cd /repo
for f in run_formal.py xdamage_native.c audit_formal.py exact_gate.py temporal_protocol.py test_temporal_protocol.py run_container.ps1 FREEZE.json; do
  git show "$SOURCE_GIT_COMMIT:research/observation_gating/xdamage_temporal_boundary_v3/$f" > "/src/$f"
done
cd /src
python3 -m unittest -v test_temporal_protocol.py
python3 run_formal.py --mode "$RUN_MODE" --sessions "$RUN_SESSIONS" --out "/results/$RUN_MODE"
python3 audit_formal.py "/results/$RUN_MODE" --source-root /src
'@
docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m --tmpfs /src:rw,nosuid,nodev,noexec,size=64m --cpus 1 --memory 2g --pids-limit 64 --security-opt no-new-privileges --cap-drop ALL -e "SOURCE_GIT_COMMIT=$SourceCommit" -e "RUN_MODE=$ContainerMode" -e "RUN_SESSIONS=$Sessions" -v "${RepoFull}:/repo:ro" -v "${OutFull}:/results:rw" --entrypoint /bin/sh $Image -ec $Inner
if ($LASTEXITCODE -ne 0) { throw "STOP_DOCKER_EXPERIMENT_EXIT_$LASTEXITCODE" }

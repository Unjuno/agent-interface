# Existing native exchange inside a private Docker desktop

This image packages dependencies for the existing native bridge, exchange,
presenter and Calc/Inkscape harness. It does not add a model runner or a second
control route. Source is mounted read-only; only the explicitly selected results
directory is writable. Each run creates its own Xvfb/Openbox and app profiles.

## Status

Container build and live use are pending local Docker Desktop engine availability.
On 2026-09-20, Docker Desktop processes were present and its configured
desktop-linux named pipe accepted a connection, but a read-only /_ping request
did not respond within 5 seconds. The original docker version/list query also
remained pending. No shared restart, container stop, prune, or new build was issued.

The dependency preflight passed on the existing WSL Ubuntu environment:
Python 3.12.3, Pillow 10.2.0, numpy 1.26.4, openpyxl 3.1.2, python-xlib 0.33,
Inkscape 1.2.2 and LibreOffice 24.2.7.2. Its first attempt unnecessarily required
xdotool; checking the actual native route showed that it uses Xlib and wmctrl,
so that unused dependency was removed. This is host-side dependency evidence,
not a container build/import/GUI result.

The dependency list follows the currently used native harness. Do not interpret
the Dockerfile or dependency preflight as a successful container experiment.
The Ubuntu tag and apt resolution are not a frozen environment: retain the built
image ID, package inventory, source commit/diff and run artifacts for experiments.

## PowerShell setup

Use this isolated worktree, not another experiment's container or shared volume.
Choose a unique container name and a fresh results directory for each allocation.

```powershell
$nativeRepo = (Get-Location).Path
$nativeName = 'agent-interface-native-own-run-01'
$nativeOut = Join-Path $nativeRepo 'results-local/docker-native-own-run-01'
New-Item -ItemType Directory -Path $nativeOut -ErrorAction Stop

docker build -t agent-interface-native-desktop:local research/live_control/docker_native
docker run -d --name $nativeName --network none --shm-size 256m --init `
  --mount "type=bind,source=$nativeRepo,target=/repo,readonly" `
  --mount "type=bind,source=$nativeOut,target=/runs" `
  agent-interface-native-desktop:local
docker exec $nativeName python3 research/live_control/docker_native/preflight.py
```

Record image identity and dependencies before task input:

```powershell
docker inspect $nativeName --format '{{.Image}}'
docker exec $nativeName dpkg-query -W
```

The dependency preflight imports the actual shared path and reads version output;
it neither starts an input task nor proves GUI readiness.

## Actual primary-assistant use

Start the existing harness in the named container:

```powershell
docker exec $nativeName python3 research/live_control/run_native_calc_self_use_v1.py `
  --app calc-inkscape --max-stages 8 --text-gap-ms 2 --probe-old-target `
  --seed 991094 --out /runs/run
```

Track this exec process until it is terminal. While it runs, use separate
docker exec calls in that same container for agent_review.py --native and
agent_exchange.py --native --review compact. Container paths in requests must
use /runs/run. Put new client request files in the selected host results folder;
the container sees them under /runs. Decode returned JSON and render its image
block; do not print base64 as text. Ground actions from actual presented images:
app versions/layouts may differ from earlier WSL results.

The resident container preserves access for final review after the harness exits.
Keep source bytes fixed during an allocation. Preserve request/reply slots;
timeouts require read-only resume, never automatic action replay.

## Cleanup

After the harness command is confirmed terminal and cleanup/results are retained:

```powershell
docker stop $nativeName
docker rm $nativeName
```

Only clean up this exact owned container. Do not prune images/volumes, stop other
experiments, or restart shared Docker Desktop to recover a pending request.
Model-dependent sensor placement and decision usefulness still require primary
model use; deterministic ordering/receipt checks can run as ordinary programs.

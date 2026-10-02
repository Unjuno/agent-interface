# WSL-native development and integration

The local Windows integration route uses Ubuntu directly for contract checks and
Linux/X11 GUI tasks. Docker Desktop is not a prerequisite. WSL 3.0.1 is the
installed WSL package version; Ubuntu still reports execution version 2. The
new WSL containers CLI (`wslc.exe`) is a separate optional isolation route.

## Fast local iteration

Keep source, virtual environments, application profiles and live capture output
in the Ubuntu filesystem. Launch commands from PowerShell with `wsl --exec`,
passing arguments directly rather than reconstructing a Bash command string.
Use the existing [native integration runner](integration_checks/README.md) and
reuse its provisioned Python environment. From the Linux repository root:

```sh
python3 -m venv .venv-native-checks
.venv-native-checks/bin/python -m pip install -r research/live_control/requirements-native-mcp.txt Pillow==10.2.0 numpy==1.26.4 python-xlib==0.33
.venv-native-checks/bin/python runtime/integration_checks/native.py --output results-local/native-check-01
```

Install dependencies once. Subsequent iterations need only the last command and
a new output path. The runner retains both complete contract suites and their
logs. Do not replace these checks with a container startup or dependency doctor.
The [current interface guide](USING_CURRENT_INTERFACE.md) describes CLI/API/MCP
routes and the existing [golden desktop demo](README.md#golden-desktop-demo-v3).
GUI work uses a caller-owned Xvfb/Openbox allocation or an explicitly selected
WSLg display, with owned-process cleanup and independent effect scoring.
Do not change display bindings or replay uncertain input during migration.

## Optional WSL containers

Use WSLc when an experiment needs an OCI image. It does not require Docker
Desktop. Inspect `wslc run --help` on the installed version: Docker options are
not all interchangeable. In 3.0.1, `--memory`, `--cpus`, `--network none` and
read-only bind mounts are available; the tested CLI does not advertise Docker's
`--read-only` root filesystem flag. A read-only source mount does not imply a
read-only container root or equivalent isolation to a frozen Docker study.
Compose support is not currently provided by WSLc.

A Windows-local directory containing the portable `runtime.pyz` can be mounted
for an explicit diagnostic run from PowerShell:

```powershell
$source = (Resolve-Path -LiteralPath '.\portable').Path
wslc run --name ai-portable-check-01 --pull never --network none --memory 512M --cpus 1 --mount "type=bind,source=$source,target=/src,readonly" python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/runtime.pyz doctor --check-dependencies
wslc inspect ai-portable-check-01
```

This exact digest must already be available, or explicitly pulled beforehand.
Use a fresh container name. Doctor exit 0 means a diagnostic completed; missing
Pillow/Xlib/MCP and no interactive display remain explicit. This example does
not certify GUI readiness. Record the image ID, command, exit and mounts.
WSLc reported that swap-limit enforcement was unavailable on this host; the
container's memory setting does not establish a combined memory-plus-swap cap.

## Resource and lifecycle policy

Use one owned GUI allocation or container experiment at a time in this integration
chat. Reuse dependencies and immutable artifacts; retain each fresh run's result.
Measure Windows available physical memory as well as Linux MemAvailable and the
WSLc VM process: Ubuntu's free RAM is not Windows's free RAM. WSLc can retain its
own VM even after a container exits. Inspect sessions before stopping them, and
never stop another chat's workload to reclaim memory.

Docker Desktop was gracefully stopped after verifying zero running containers;
its automatic startup was already disabled. Images, volumes, stopped containers
and historical frozen evidence remain preserved. New local integration runs use
Ubuntu; optional isolated runs use WSLc. Existing research workflows that require
a frozen Docker image/environment remain historical or separately scoped, and
are not silently relabeled as WSLc results.

The initial migration did not change global `.wslconfig`. A subsequent local
confirmation staged the following host budget on this 16 GB Windows machine:

```ini
[wsl2]
memory=6GB
swap=2GB
[experimental]
autoMemoryReclaim=dropCache
```

These are host-specific settings, not project defaults. The running Ubuntu VM
still reports approximately 7.6 GiB total RAM; the 6 GB cap remains pending a
complete WSL stop/start. Other MCP servers are active, so no global shutdown was
performed. At a coordinated idle boundary, stop owned work, run `wsl --shutdown`,
and start Ubuntu again. Check `/proc/meminfo` after starting it before declaring
the cap active. Global limits affect all WSL2 distros; swap uses host disk space.
A configured cap alone does not prove that peak memory or OOMs improved.

[Native migration confirmation](results/wsl-native-migration-confirmation-20261002-01/README.md)
retains the 409 protocol and 192 harness checks, staged configuration and host
snapshot. Optional WSLc memory enforcement was inadequate in the prior host
experiment, so Ubuntu direct execution is the normal integration route.

[Migration evidence](results/wsl301-docker-free-migration-01/README.md) records the
native suite result and actual bounded WSLc launch. No matched Docker/WSLc speed,
peak-memory, provider-token or application-success improvement is established.

References: [WSL 3.0.1](https://github.com/microsoft/WSL/releases/tag/3.0.1),
[WSL containers GA](https://blogs.windows.com/windowsdeveloper/2026/09/29/wsl-containers-now-generally-available/),
[WSL configuration](https://learn.microsoft.com/en-us/windows/wsl/wsl-config).

## Repeat checks from Windows without reinstalling dependencies

Use [wsl-native.ps1](integration_checks/wsl-native.ps1) with an absolute Linux
repository path and a fresh result directory:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ./runtime/integration_checks/wsl-native.ps1 `
  -Repository /var/tmp/agent-interface-evidence-storage-main `
  -Output results-local/native-iteration-01
```

The explicit process-scoped execution policy also permits the inspected script
when the checkout is accessed through a WSL UNC path; it does not change the
host execution policy. Direct UNC invocation was refused by this host policy
before any suite started.

This forwards to the same native runner, propagates its exit code and never
builds an image or installs dependencies. Interpreter paths are overridable.
If the reused environment is absent, provision it once using the commands above;
subsequent iterations reuse it. Keep live profiles and output in the Linux
filesystem. Existing registered integration MCP configuration already launches
`wsl.exe --cd /var/tmp/agent-interface-integrated-main --exec ...native_mcp_v1.py`;
it requires no Docker daemon. This evidence checkout is a separate source path.

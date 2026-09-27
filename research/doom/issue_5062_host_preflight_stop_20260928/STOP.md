# Issue #5062 host preflight — STOP

Date: 2026-09-28. Allocation: the proposed #5062 real-socket lease-margin construction.

## H/T/D/C/U

- **H:** The pinned production sender/exchange/Lease boundary can be exercised under the preregistered Ubuntu 22.04 WSL2 + Docker Desktop Linux/amd64 host and transport.
- **T:** Read-only host inspection only. Commands: `docker context show`; `docker info --format '{{.OSType}}/{{.Architecture}} {{.OperatingSystem}}'`; `wsl.exe --list --verbose`; `wsl.exe -d Ubuntu -- sh -lc 'cat /etc/os-release; docker context show; docker info --format "{{.OSType}}/{{.Architecture}} {{.OperatingSystem}}"; python3 --version'`. Read and fetched the exact source blobs declared in #5062: sender `096adf9b60eaf6a31fe92c836f57d1a4d26b177e`, exchange `267b5ccce24ca43b8a6e9b36219d50342888aa27`, Lease `b9dac6bb4063928354733d79bf371909a288a3d1`.
- **D:** `STOP_HOST_ENVIRONMENT_MISMATCH`. Windows Docker context is `desktop-linux`, Docker Desktop reports linux/x86_64; WSL integration connects to the same Docker Desktop daemon. Installed WSL distro `Ubuntu` is `Ubuntu 24.04.4 LTS` (Noble), Python `3.12.3`, not the preregistered Ubuntu 22.04 host. The distro list exposes no Ubuntu 22.04 distribution. No container, Unix socket, clock probe, Lease request, model, GUI, game, or physical input was started.
- **C:** This is a pre-invocation environment STOP only. It is neither a result for any deadline arm nor evidence that the sender/Lease hypothesis failed. No exact 22.04 WSL host is currently available through the observed installed distro set.
- **U:** Whether a user-installed Ubuntu 22.04 WSL distro or a separately authorized 24.04 successor is available remains unknown. Do not silently substitute Ubuntu 24.04, run inside an Ubuntu container and call it WSL-host evidence, or reuse the allocation after changing the host.

The allocation remains unspent at the experiment boundary and requires a new frozen successor if host environment changes. Preserve #5054/#5058/#5062 source and gates unchanged.


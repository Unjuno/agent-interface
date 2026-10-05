# T0a environment record

Captured on 2026-10-05 before candidate execution.

- Repository HEAD: `f9fb28932226a0d12c1200f8b9215f7e89993849`.
- Host: macOS, arm64.
- Python: captured exactly in `FREEZE.json`.
- Docker context: `orbstack`; `docker info` reported `29.4.0 OrbStack aarch64`.
- Read-only `docker ps` failed because the daemon could not open an existing
  containerd content blob and returned `operation not supported` (full output
  was observed in this turn). No image/container/VM mutation or retry was made.

The proposal explicitly allows a CPU-only standard-library finite model. The
experiment is run with the local Python interpreter and is **not** described
as container-backed or equivalent to a runtime allocation.

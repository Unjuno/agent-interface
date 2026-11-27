# Runtime preflight

Host: macOS 27.0.1 arm64, kernel 27.0.0. The fixture uses only deterministic standard-library Python and has no OS, GUI, network, runtime, or input dependency.

OrbStack context was `orbstack`; Docker Engine reported 29.4.0 linux/arm64. Image listing and inspection of the already referenced `python:3.11-slim` failed with containerd content-blob errors (`operation not supported`). No image pull, prune, repair, or Docker mutation was attempted. Since the Issue's stop condition explicitly allows a frozen local/container result and this fixture does not require container-specific behavior, formal execution uses the exact host Python executable/version recorded in `FREEZE.json`. The runtime probe outputs and hashes are frozen there.

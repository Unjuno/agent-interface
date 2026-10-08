# Docker-free WSL migration confirmation, 2026-10-02

The existing production integration route was exercised directly in Ubuntu on WSL 3.0.1.0. Docker Desktop was not running. The protocol and harness suites passed with reused interpreters; full logs, return codes and SHA256 identities are retained. This is a contract check, not a GUI task or Docker performance comparison.

Host memory snapshot and Linux meminfo are separate point-in-time measurements. A new host .wslconfig stages memory=6GB, swap=2GB, autoMemoryReclaim=dropCache. These settings apply globally and remain pending until the next complete WSL stop/start. No global shutdown was performed during other agents' workloads. The configuration is reversible by restoring the previous absent .wslconfig after preserving any later edits. No Docker images, volumes, stopped containers or historical results were deleted.

Native Ubuntu is the normal iteration route. WSLc remains optional when an OCI image is required; prior evidence found memory-limit enforcement inadequate on this host. Flag acceptance is not proof of an enforced ceiling. Historical Docker protocols and hosted CI are not rewritten as native results.

No speedup, reduced peak memory, resolved host OOM or token savings is inferred. Source and checks are recorded in verification.json. This retained confirmation is published with the WSL iteration launcher. Its source pin and staged configuration remain historical; later launcher checks are recorded separately.

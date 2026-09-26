# STOP — PMU preflight returned no counter data

The first container compiled the probe but `/tmp` was mounted `noexec`; it stopped with `Permission denied` before the PMU program ran (`preflight.log`). A corrected container invocation used an executable isolated tmpfs, but Docker returned `error waiting for container: unexpected EOF`; immediately afterward the OrbStack Docker socket was absent. No counter output was retained, so this is **not** evidence that PMCCNTR is available or unavailable.

Read-only checks showed OrbStack status `Running`, a restored Docker socket, Docker Engine 29.4.0 linux/aarch64, and a later `--entrypoint true` container completed (`runtime-smoke.log`). We did not repeat the PMU instruction after the runtime disconnection. No ViZDoom game, WAD, capability, or formal allocation was used. Disposition: `STOP_RUNTIME_DISCONNECTED_DURING_PREFLIGHT`; PMU capability remains unknown; formal rows remain 0/120.

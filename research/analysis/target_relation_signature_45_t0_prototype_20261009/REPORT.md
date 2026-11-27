# #45 relation-signature prototype — construction result

## Disposition

Prototype implementation complete; no formal T0 result is claimed. A standalone advisory matcher accepts one exact fresh relation-signature match, returns `AMBIGUOUS` for duplicate exact matches, returns `UNKNOWN` when a compatible target's relations changed, and rejects cross-container candidates. Its result always carries `authority: none`.

Seven authored tests pass under CPython 3.12.13 on macOS 27.0.1 arm64, both normally and with `python -O`; `py_compile` and repository strict analysis-index validation pass. Test stdout is retained in `CONSTRUCTION_NORMAL.txt` and `CONSTRUCTION_OPTIMIZED.txt`.

This is standalone construction evidence only. The matcher is not connected to the runtime, action admission, GUI, app, or model. It does not validate the trust, completeness, or semantic meaning of any real UI relation witness and does not measure false-bind rates or grounding cost.

## Why formal T0 was not run

Current OrbStack `docker info` succeeded, but read-only `docker ps` and `docker images` inventory failed with containerd blob read errors (`operation not supported`). The presence or absence of other workers' containers therefore could not be safely determined. No container was created, stopped, or modified, and no experiment was substituted onto the host. A separately isolated and inventory-readable lane is required before any formal T0 allocation.

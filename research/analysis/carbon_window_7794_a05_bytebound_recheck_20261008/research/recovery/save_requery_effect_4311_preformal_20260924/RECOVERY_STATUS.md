# Recovery status — save requery to guarded continuation (#4311)

Recovered from remote branch
`research/save-requery-effect-2869-20260924-w6d3`, tip
`335bedf634`. The branch contains only the exact public preformal source
capsule; it has no formal results or raw evidence.

## Source recovery and local checks

- The original eight repository files (README, source manifest, five source
  chunks, and unpacker) are retained byte-for-byte under this recovery path.
- The source capsule restored 16 files and matched its declared archive
  SHA-256 `5bade3a1ca928e69dd1aee1385fcbcc258d72c35db7c99a1fa1318c9f9cd0309`.
- Source-only Python syntax/JSON checks and 21 deterministic unit tests passed.
  No Tk/Xvfb case, launcher batch, or formal allocation was run in this
  recovery session.

## Formal allocation disposition

The frozen capsule declares `save-requery-effect-4311-20260924-w6d3`,
formal 0/24 before execution, and an expected Linux x86_64 environment with
CPython 3.13.5, Tk 8.6, Python-Xlib 0.15, and an Xvfb binary hash. On
2026-10-01 the available host was macOS arm64; OrbStack reported Running but
had no Linux machine available to `orb run`, and the Docker Unix-socket
`/_ping` request timed out. No matching isolated Linux execution environment
was available, so I did not substitute host execution or alter the freeze.

Recovery disposition is `HOLD_PRE_FORMAL_ENVIRONMENT_UNAVAILABLE`, not a
scientific PASS/FAIL. The formal allocation remains unconsumed; any future
execution must first establish the frozen environment and preserve the
original commands/gates. Issue #4311 remains OPEN. Later #4319/#4321 records
are separate allocations and are not substituted for this one.

This is source/provenance preservation only. It changes no runtime code and
makes no task-effect, reliability, latency, model, or product claim.

# Crash-atomic suppression persistence — Issue #5795 T0

This package tests only a finite single-process `SIGKILL`/restart fixture. It
does not test power loss, multi-writer serialization, an application runtime,
expiry timing/garbage collection, GUI effects, or product safety. The schedule
tests explicit retirement with a retained tombstone, not GC. The host matrix is construction evidence only;
formal candidate and auditor counts remain 0/0 until an explicit isolated
Obstac allocation is recorded on Issue #5795.

## Files

- `FREEZE.md`: H/T/D/C/U, frozen schedule and decision boundaries.
- `FREEZE.json`: executable hash/runtime manifest. It must be created only
  after all source files and an exact assigned guest endpoint are frozen.
- `protocol.py`, `worker.py`, `runner.py`: case schedule and toy candidate arms.
- `audit.py`: raw-only auditor; imports none of the candidate or protocol code.
- `container_runner.py`: bounded, network-disabled candidate and separate
  auditor Docker invocations. Formal mode refuses absent/mismatched allocation
  metadata before invoking Docker.
- `CONSTRUCTION.md`: host-only rehearsal result, failures and allocation status.
- `SHA256SUMS`: source/freeze-file hashes for local verification.

## Construction checks

The optional container construction path itself requires an explicitly named
isolated construction context/endpoint in `OBSTAC_CONSTRUCTION_CONTEXT` and
`OBSTAC_CONSTRUCTION_DOCKER_HOST`; it never defaults to the shared OrbStack
context. No endpoint is currently assigned, so the host-only matrix is what has
been exercised. Construction mode does not require `FREEZE.json` and writes no
formal rows.

From repository root:

```sh
python3 -B -m unittest discover -s research/experiments/crash_atomic_suppression_5789_t0 -p 'test_*.py' -v
python3 -B -m py_compile research/experiments/crash_atomic_suppression_5789_t0/*.py
git diff --check
python3 research/analysis/check_index.py
```

Host-only checks never count as formal rows. The candidate container uses the
pinned `python:3.12-slim` Linux/arm64 image, one CPU, 256 MiB, 64 PIDs, no
network, read-only root and source, and a dedicated output mount. The auditor
runs only after a zero candidate exit, in a separate container with read-only
source/raw input and a distinct output mount.

Do not use the shared OrbStack context merely because it exists. Formal mode
requires an exact non-overlapping allocation naming owner, context and daemon
endpoint; it verifies those values and all source/schedule/auditor/image hashes
against `FREEZE.json`. A missing endpoint is STOP, not a reason to probe Docker.
After allocation, create the manifest once, update hashes and Issue #5795,
then execute the frozen candidate exactly once and preserve the independent
audit plus every STOP/FAIL unchanged.

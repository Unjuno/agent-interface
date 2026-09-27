# Issue #3924 — OrbStack broker contract result

## Decision

`STOP_FAKE_EXECUTABLE_MOUNT_MISSING` (formal allocation 02). This is not a
scientific PASS or FAIL for the zero-exit hypothesis. The formal matrix was
executed once and retained; it is not rerun under this allocation.

## What ran

The exact current-main broker and frozen fake-only runner ran inside OrbStack
29.4.0 / linux-arm64, Python 3.12 image ID
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
with `--network none`, read-only root/source, 1 CPU, 256 MiB memory and swap,
32 PIDs, no capabilities, and no-new-privileges. The formal runner itself
completed seven planned rows. No real Codex/model/provider, GUI, host input, or
credentials were available or invoked.

The separate raw-only auditor ran in a second container with the same image and
isolation policy. It recomputed hashes for 41 retained raw files and returned
`HOLD_AUDIT_ERRORS errors=9`.

## Evidence interpretation

- Every nominal fake-backed row (`exit0`, `exit23`, `timeout`, and `two-queued`)
  pointed `CODEX_EXE` at `/study/fake_codex.py`, but allocation 02 mounted the
  checkout only at `/repo`. The receipts therefore contain
  `FileNotFoundError` / `HOST_BROKER_EXECUTABLE_UNAVAILABLE`; there are zero fake
  invocation records. These rows do not test fake exit propagation or timeout.
- The explicit `unavailable` row correctly records the typed
  `HOST_BROKER_EXECUTABLE_UNAVAILABLE` receipt for its intentionally missing
  executable. This is a narrow typed-unavailable observation only.
- The `malformed` row fails closed with `KeyError: 'schema'`, process code 1,
  and no broker receipt or response.
- The `two-queued` row emits exactly one response and receipt for `queued-a`
  and leaves `queued-b` queued, but the child could not start. This supports
  only the one-shot request-selection/cardinality observation.
- The `one-shot-idle` row emits no receipt or response and is stopped by the
  external 300 ms harness bound (SIGKILL / -9). It does not exit by itself.

The audit errors preserve the missing-fake evidence; they are not silently
treated as passing contract checks. Because provenance for fake-backed cases
failed, no conclusion about zero-exit propagation is made.

## Retained artifacts

- `formal_run_02/formal/`: request and response bytes, broker receipts,
  process results, fake invocation records where present, and
  `AUDIT.json` with per-file hashes.
- `formal_run_01/FORMAL_RUN_STOP.json`: earlier pre-case runner/freeze schema
  STOP; formal cases 0.
- `FREEZE.json` and `FREEZE_02.json`: both preregistrations, preserving the
  first preflight STOP and the second allocation's frozen source/gates.

The corrected `--study` mount and any fresh allocation require a new explicit
preregistration and independent review. This result does not authorize a
production broker edit.

# Recovery and disposition — 2026-09-30

This is an archival recovery of the existing preformal record for Issue #3190,
not a new experiment and not a PASS. The six files from remote branch
`research/desktop-lifecycle-rebind-3190-20260922-v1` are preserved unchanged.

## Verified state

- Original branch head: `2656e11be06b26280ccc7233505ccea8cb0adb95`.
- Issue #3190 remains open. Its latest recorded formal invocation count is 0.
- Host CPython 3.14.5 rerun of the two excluded synthetic construction tests:
  2/2 passed. This does not run the frozen source audit or satisfy its formal
  gate.
- Against current `main` at intake `7fcf30f37e122bc3fce7ab893aebd9bfa4a864a8`,
  the frozen four-source manifest matches 3/4 Git blob identities. The
  `runtime/cli_v1/api.py` pin is stale: expected
  `47193afd3bdb5e8bef91bf539f74f180ce9b9406`, current
  `a74962ceaf6366138a28ffee0c8cf80523c300f9`.
- Therefore do not run the frozen audit against current `main` or report a
  current-source PASS. Disposition remains
  `STOP_STALE_FROZEN_SOURCE_BEFORE_FORMAL`; no GUI, model, input, or formal
  operation was performed here.

## Validation boundary

`python3 -B -m unittest -v test_audit` passed 2/2 on the preserved source on
the host. These are synthetic audit-construction tests only. The original
source manifest, audit, plan, environment record, and tests remain byte-for-byte
as committed on the predecessor branch. A later prospectively frozen allocation
would need a fresh current-main source pin and the full independent corruption
gate; do not silently edit this predecessor freeze.

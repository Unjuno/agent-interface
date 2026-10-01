# Recovery status — 2026-10-01

The original 12-path source/freeze package is preserved byte-for-byte. Its
independent compatibility implementation, frozen candidate/CLI/ledger inputs,
tests, audit, and controls are all present. On the available CPython 3.13.14
host, the six source unit tests pass when the exact existing main dependencies
(`research/integration/event_inbox_reader_v1` and
`research/live_control/delivery_ledger_v2.py`) are included in the checkout.

**Original engineering-result publication: HOLD.** The owned source branch
does not contain the one-invocation raw compatibility matrix or its independent
audit/control outputs. Issue #4399 reports those results, but this recovery did
not reconstruct or re-audit the reported 523-case/400-block data and does not
claim the reported CPU ratio as independently verified. No compatibility
invocation or prior performance allocation was rerun.

This is a source-and-unit-test preservation record only. It does not promote a
scientific/performance result, alter the freeze, or authorize runtime adoption.
The exact raw/audit/control bundle remains the outstanding delivery gate.

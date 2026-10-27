# Issue #1998 A02 focused payload size experiment

This additive allocation complements the retained #1998 request-validation fixture with a serialized-byte comparison against a full-frame payload. It independently verifies exact crop pixels and fail-closed handling of stale, replaced, focus-lost, ambiguous, and out-of-bounds requests. No GUI or action is involved.

See `PROTOCOL.md`, `FREEZE.json`, and the retained `results/` artifacts. Results are synthetic byte-accounting evidence only.

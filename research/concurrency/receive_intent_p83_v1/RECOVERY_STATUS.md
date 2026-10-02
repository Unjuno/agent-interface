# Current publication status — Issue #4335

This is a source-only recovery of the exact frozen p83 allocation. It does
not promote the Issue-reported result without the formal evidence package.

## Source capsule verification

The four committed parts restore to the declared 17,748-byte XZ archive with
SHA-256 `3cb9dc533acc5dc8755ec18f5e67b7100e92c52cf5967e0067ddc73a085e53ef`.
All nine embedded member hashes match `SOURCE.json`; the five Python members
syntax-compile in a Python 3.13.5 ARM64 container. No study actor or formal
batch was run.

## Formal evidence boundary

Issue #4335 reports `PASS_PREBODY_RECEIVE_INTENT_SCOPED` for 24 cases, but the
audited branch contains only `SOURCE.json` and its four source parts; formal
raw, database/IPC/process receipts, audit, and controls output are absent.
Those historical Issue summaries are not reconstructed raw evidence.

Repository status is **HOLD_FORMAL_RESULT_PACKAGE_MISSING** pending exact
result bytes and read-only audit reproduction. No rows were synthesized or
rerun. The bounded receiver-restart result is not a general exactly-once,
power-loss, or production claim. Issue #4335 remains open.

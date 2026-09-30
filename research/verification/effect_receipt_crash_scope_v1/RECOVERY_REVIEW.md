# Recovery review: Issue #3991 effect/receipt transaction scope

The original 2026-09-22 branch contains only the preformal `FREEZE.json`. It
binds eight source/plan/environment identities, but those payloads, the 75
formal cases, batch receipts, raw database/journal bytes, and audit outputs
were not present on the branch, current `main`, or in a bounded search of
accessible local workspace/temp/download paths.

## Issue-reported formal result

Issue [#3991](https://github.com/Unjuno/agent-interface/issues/3991),
comment [5766708960](https://github.com/Unjuno/agent-interface/issues/3991#issuecomment-5766708960),
reports six once-only batches with exit codes `[0,0,0,0,0,0]`, 75/75 cases,
270 child exits, 75 read-only queries, and
`PASS_EFFECT_RECEIPT_TRANSACTION_SCOPE_SCOPED`. It reports 11 formal evidence
tests passing and raw JSONL SHA-256
`b1bd1bfdd3c48034d061fdb2355f91e52be10c3b41b2e5810b6963f2233b9999`.

The same comment distinguishes unsafe comparison outcomes: EFFECT_FIRST and
ATOMIC_EXTERNAL each produced six duplicate effects after recovery;
RECEIPT_FIRST produced six false COMPLETED results with zero effect; only
ATOMIC_LOCAL had exactly one effect in all 15 cases. These are Issue-reported
counts, not independently recomputed here. The raw bytes and audit outputs
were unavailable, so the hash, counts, and scoped decision remain unverified
from repository-resident formal evidence. No production, distributed
exactly-once, or power-loss claim follows.

## Separate attachment warning

Issue #3991 also mentions a conversation attachment for a distinct
45-case `attempt_effect_commit_crash_v1` allocation. That study is not this
75-case allocation and is not used as its evidence or substitute. It was not
found at the named local download path during this recovery.

## Recovery boundary

`FREEZE.json` is preserved byte-for-byte. No SQLite worker, crash batch,
formal run, retry, or recovery operation was started. Keep the Issue-reported
outcome distinct from independently verified evidence; do not rerun the
consumed allocation merely to recreate missing outputs.

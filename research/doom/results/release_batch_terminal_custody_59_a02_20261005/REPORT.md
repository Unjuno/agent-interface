# Release-batch terminal custody A02 — 2026-10-05

## Claim and hypothesis

A terminal must preserve the identity and custody of every release-batch publication involved in its worker and cleanup paths. The worker failure remains the primary terminal error; a distinct cleanup publication must be recorded separately. A completed program's ledger must not appear in a later program's release result when that later program has no active release context.

## Test and decision

The frozen parent was PR #7635 head `dd5e7fa4b26c66fe1de3bfa24152ad8e4e8a9cfd` (branch `research/release-sink-delivery-20261004`). Three focused regressions were added:

1. Worker `KeyboardInterrupt` with ledger A followed by cleanup `SystemExit` with ledger B: terminal keeps A as `release_batch_delivery`, B as `release_batch_cleanup_delivery`, reports the worker error, clears the active slot, and re-raises the same worker exception.
2. Worker `OSError` with ledger A followed by verified cleanup returning ledger B: terminal retains both ledgers with the same field split and reports the worker error.
3. A completed `program-1` publishes its three release receipts and clears its thread-local context; a later context-free `release_all()` must not return `program-1`'s cached ledger.

All three custody regressions failed against the frozen parent. After the candidate repair, the ExecutorV13 suite passed 13/13 and the release-backend composition suite passed 11/11 (24/24 combined). The release-sink regression now sweeps all three positions under both accept-before-raise and reject-before-raise, asserting confirmed/unknown/not-attempted custody and no retry. All four affected Python files compiled, and `git -c core.whitespace=cr-at-eol diff --check` passed. `GREEN_OUTPUT.txt`, `COMPILE_OUTPUT.txt`, and `SHA256SUMS` retain the exact output and tested source/test hashes; `RED_OUTPUT.txt` retains the expected pre-fix failures.

## Change and limits

ExecutorV13 now keeps worker and cleanup custody in distinct terminal fields, preserves the worker exception as the primary `error`, and still re-raises the original process-level exception after terminal publication. The release backend only attaches a ledger from the current release context; it no longer falls back to the last program's cached ledger when the current context is absent. Incomplete-batch failures retain custody on their original exception, so a later context-free cleanup call cannot misattribute that ledger.

These are deterministic synthetic backend/executor tests. They do not measure how often both failures occur in a live runtime and do not establish physical release, GUI/application effects, game progress, or live-control success. No model, GUI, OS input, game, or allocation was used.

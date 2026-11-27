# V39 post-batch keymap fault recovery A06

## Hypothesis

The consumed A05 run stopped because its fake XTest wrapper suppressed both the explicit SPACE key-up and the owner's cleanup key-up, while its runner deferred persistence until all cases completed. A one-shot drop should leave the explicit edge missing but allow cleanup to release SPACE; each completed case should remain auditable even if the final unavailable-query case stops.

## Test

On current main frozen before execution, run three fresh fake-display cases through the production V39 release-batch backend and V4/V3/current V12 owner: normal two-key release; drop exactly one explicit SPACE `KeyRelease` and allow cleanup to retry; and fail the next cleanup `query_keymap` after the batch. Append and fsync each case before advancing. No candidate retry is allowed.

## Decision

PASS the narrow harness-recovery gate only if the normal case completes, the one-shot drop is observed exactly once and cleanup returns verified with an empty fake key set, and the query-failure case is retained as an explicit HOLD row without erasing earlier cases. A missing prior case or an unexpected second dropped release is STOP.

## Limits

This is a deterministic fake-Xlib construction test. It does not establish physical key state, application consumption, live latency, useful feedback, recovery under threat, or MAP01 behavior, and does not grant or consume a live-game allocation.

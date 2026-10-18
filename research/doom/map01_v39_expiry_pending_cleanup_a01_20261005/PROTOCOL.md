# A01 protocol — expiry cleanup still pending when execute exits

## H / T / D / C / U

**H.** The current PR #7805 bridge's unconditional one-time drain in `execute()`'s `finally` is insufficient when InputOwner has begun expiry cleanup but is blocked before it appends the `owner_release` record. The confirmed per-key-up receipt will exist at the owner by the time ExecutorV12 finishes its terminal release barrier, but the bridge will not emit it before the expired terminal.

**T.** Freeze current main `aa2e4b623b2f4ccdcbc8e294535bab09c0092f30`, PR #7805 head `7a696dc085cad8a49eaae50d968bc6e8d28fb45e`, and the pinned source hashes in `SOURCE_LOCK.json`. On fake Xlib, admit one F8 down, let the owner reach its lease-expiry cleanup, block the cleanup's release `sync()`, allow backend `execute()` to observe expiry and exit, verify the backend `release_all()` call is queued, then unblock sync. Record bridge events, owner records, terminal, and final fake state. Run exactly one candidate invocation and a separate raw-only audit.

**D.** Evidence of the hypothesized gap requires: one context/actuation-bound down; the expiry owner's record contains exactly one `CONFIRMED_PHYSICAL_UP` with matching id/step/token/actuation id; its verified-empty owner record completes before a single `expired` terminal; the bridge event stream contains zero matching `input_release_measurement` rows; and final physical/held state is empty. Any deviation is `NOT_REPRODUCED` or `FAIL` under the audit, not promoted as the hypothesized gap.

**C.** Test-only fake Xlib; synchronization is deliberately delayed at `sync()` after the fake KeyRelease is applied but before owner record publication. The executor uses current-main ExecutorV12. The backend's `release_all` test seam exactly mirrors the pinned `session_v5.Backend.release_all` implementation (`owner.call('release', lease)`, then clear held). No actual display, OS input, game, or live allocation.

**U.** This tests a synthetic cleanup/telemetry race only. It does not establish this ordering on live X11, application/game effect, useful feedback, recovery efficacy, threat response, latency, MAP01 progress, or Issue #59 completion. OrbStack had a confirmed pre-start image-blob `operation not supported` failure in the immediately preceding experiment; this study does not repeat the identical failing container invocation and uses an explicitly labeled native fallback.

## Execution discipline

Preflight performs imports and opens/closes only a fake owner; it sends no key events. Formal candidate path is write-once and is invoked once. The auditor reads only retained JSON and never calls candidate code. A failed candidate invocation is preserved and not retried in this run ID.

## A02 successor probe (separate write-once run ID)

A02 preserves A01 and tests one minimal experimental delta: subclass `release_all()` delegates to the pinned implementation and drains owner records in `finally`. It repeats the same fake-display sync gate, distinct program/intent IDs, and one-shot raw-output path `results/formal_02/`. Its auditor requires exactly one matching per-key up measurement before the expired terminal, the independently verified owner record, no aggregate release event, and empty final fake/held state. A02 PASS is limited to this synthetic ordering and is not a production or live-control claim. The A02 candidate is likewise invoked once; a failed invocation is retained and not retried.

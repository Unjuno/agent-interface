# V39 stale Executor rejection recovery — current-main A01

## Change

When an action segment's Executor submission is rejected with `latest observation sequence required before input`, V39 now treats it as a no-admission outcome. It drains a bounded backlog and obtains a newer full observation, records the rejection in final admission and the running-action guard, retains any already completed segment receipts, discards the remaining stale action, and continues to the next bounded controller iteration for a fresh planner decision. Non-stale rejections remain fatal. If backlog recovery exhausts its four-batch limit, the controller fails closed.

The rejection timestamp is `controller_received_ns`, captured when the ACK wait returns; it is not mislabeled as a transport timestamp. The first rejected segment records no historical admission. A stale rejection after a previously completed segment preserves that historical acceptance while removing current authority.

## H / T / D / C / U

**H.** A stale sequence rejected before Executor worker creation should discard the candidate and recover to a newer observation and new decision, while preserving no-input and prior release/history invariants.

**T.** Focused tests exercise the production stale-rejection recovery helper, final-admission receipt, running-action guard in both READY and BETWEEN states, finite backlog exhaustion, and AST-verified controller wiring for primary and fallback action segments.

**D.** Scoped local pass. The exact current-main V39/controller and action-guard suites pass 63/63 in normal Python 3.13 and 63/63 under `-O`. Recovery requires a strictly newer full observation, stale-only rejection matching, and bounded queue-drain completion. Both a fresh action rejection and a rejection after prior completed work retain no current input authority; prior admitted segment history is preserved.

**C.** Deterministic queues, real controller helper/state machines, source-level checks for caller routing. This is not a live scheduler distribution or an Executor process run.

**U.** No App Server, model, Doom/MAP01, GUI, OS input, physical key release, useful task effect, survival, or live allocation was run. The patch handles stale rejection at active action segment submissions and between-segment passive observation submissions. Stale rejection at the earlier pre-planner cover submission remains outside this change. Issue #59 remains open and live gates are unresolved.

## Reproduce

```powershell
py -3 -m unittest research.doom.v39_stale_ack_recovery_currentmain_a01_20261008.test_stale_rejection_recovery -v
py -3 -O -m unittest research.doom.v39_stale_ack_recovery_currentmain_a01_20261008.test_stale_rejection_recovery -v
```

The retained full regression commands and outputs are `normal-tests.txt` and `optimized-tests.txt`.

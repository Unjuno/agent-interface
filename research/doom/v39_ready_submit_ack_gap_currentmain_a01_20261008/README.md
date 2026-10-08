# V39 ready-to-submit acknowledgement gap — current-main A01

## H / T / D / C / U

**H.** An observation may be consumed during the action-acceptance wait after final freshness admission. Executor rejects an obsolete sequence before worker creation, but the controller wait has no action monitor and the existing rejection path raises instead of returning to a fresh planner decision.

**T.** The package runs the exact current-main nested `wait()` function on an ordered typed observation, full observation, and stale-sequence rejection. It checks the actual `execute_segment` acknowledgement-wait callsite and the production `ExecutorV12.submit` ordering (sequence check before worker construction). Normal Python and `-O` both run the same two checks.

**D.** Scoped reproduction: the wait consumes the typed observation with zero monitor calls, updates `latest` from the full observation, and returns the stale-sequence rejection. Executor source rejects before worker creation. Current controller code raises at that rejection; no automatic fresh planner retry is present in that path.

**C.** Exact wait helper plus AST checks against frozen current-main source. The fake queue fixes event ordering; this is not an observed scheduling frequency or real executor run.

**U.** No model, game, GUI, OS input, physical release, task effect, or live allocation. The finding identifies a missed replan opportunity, while Executor rejection is fail-closed for that submission. A production repair needs an explicit stale-rejection recovery state that discards the old action, drains to a fresh observation, preserves release guarantees, and begins a new planner decision under a finite retry budget.

## Reproduce

```powershell
py -3 -m unittest research.doom.v39_ready_submit_ack_gap_currentmain_a01_20261008.test_ack_gap -v
py -3 -O -m unittest research.doom.v39_ready_submit_ack_gap_currentmain_a01_20261008.test_ack_gap -v
```

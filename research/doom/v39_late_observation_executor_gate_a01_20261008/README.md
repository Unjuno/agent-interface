# Issue #59 V39 late-observation executor gate A01

This construction check follows a stale-action readiness schedule through the current-main Executor freshness guard. The producer increments `Backend.sequence` before it emits a new typed observation. The controller's pending-future completion path can snapshot a finite queue backlog, retain an older full observation as `latest`, and later submit with that older sequence. The exact current-main `Executor.submit` method and nested controller `execute_segment` function are AST-executed with expected sequence 1 and backend sequence 2.

Result: the Executor raises `ValueError("latest observation sequence required before input")` before validation, admission event publication, worker startup, or input. This establishes a fail-closed freshness barrier for this schedule. The controller's exact `execute_segment` function maps the `rejected` response to `RuntimeError`; the executed branch makes one submit attempt and has no retry/accept event. Thus stale input is prevented, while successful fresh replanning/session continuity is not established by this test.

The schedule basis is the earlier current-main late-observation A03 construction result, which stopped at pre-executor READY with source sequence 1 and late health observation sequence 2. This A01 check does not rerun that queue interleaving; it tests the next production boundary using exact current-main producer and executor source identities.

## Scope limits

Synthetic scheduling only. The exact current-main `Executor.submit` method is executed. Controller/producer flow is source-checked; the full backend, session process, queue, GUI, OS input, game, planner, model, live HUD cadence, recovery, progress, and terminal outcome are not run. No live authorization is implied. The V39 threat-exposure gate in #59 remains open.

## Reproduction

Run `python3 run.py`, then `python3 verify.py`. The source files are vendored byte-for-byte from the frozen main commit identified in `FREEZE.json`. A container-backed repeat was attempted but stopped before image inspection because OrbStack content-store accounting returned `operation not supported`; see `CONTAINER_STOP.txt`. The same construction/audit ran on the host.

# Adjustable-autonomy responsibility handoff — Issue #5324 T0

## H / T / D / C / U

**H.** Explicit acceptance and quiescence boundaries can reduce modeled no-owner gaps and duplicate-owner intervals relative to route-only or acknowledgement-only transfer while retaining more eligible work than an always-stop/no-owner policy.

**T.** A deterministic, authority-neutral finite simulator executes the same 13 event schedules against five explicitly operationalized policies: `ROUTE_ONLY`, `ACK_ONLY`, `TWO_PHASE`, `THREE_PHASE`, and `FAIL_CLOSED_NO_OWNER`. The schedules cover nominal transfer, offer loss, refusal, source/target crash before and after acceptance, commit loss, stale snapshot, expiry, duplicate acceptance, concurrent human intervention, and failed-target reclaim. No model, GUI, task input, Docker, GPU, or external service is used. All times are logical ticks, not wall-clock latency.

**Novelty boundary.** Merged #5320/#5326 already tested lifecycle protocol fidelity (release/acquire/expiry/retry/unknown) across finite monitor policies. It did not model responsibility moving from one actor to another, an acceptance/quiescence interval, fallback ownership, or human takeover. This T0 tests only that distinct handoff boundary; it does not repeat or modify #5320's matrix.

**D.** `PASS_HANDOFF_BOUNDARIES_SCOPED` requires zero duplicate-owner ticks and zero false task-success claims in the two-/three-phase policies; fewer total no-owner ticks than always-stop on nominal, lost-offer, and reclaim schedules; and the independent oracle to reconcile every actor-state trace. `FAIL_DUPLICATE_OWNER` or `FAIL_FALSE_SUCCESS_CLAIM` takes precedence. `HOLD_NO_DISTINGUISHING_VALUE` if neither explicit protocol improves an eligible schedule over route-only/ack-only. This T0 cannot claim empirical responsibility transfer or GUI task success.

**C.** The model assumes a single logical task, one source, one target, and an optional human fallback; fixed discrete event schedules; messages can be omitted or delayed by schedule; and ownership changes only on named protocol events. Protocol behaviors below are definitions under test, not claims about existing runtime code.

**U.** Two automation actors, one human proxy, bounded schedules, crash/loss/expiry faults, one live task-demand bit, no real clocks, no human attention model, no tool/backend enforcement, and no empirical task effect. T1 is not authorized by this T0.

## Tested policy definitions

- `ROUTE_ONLY`: source relinquishes at route request; target becomes active on offer delivery, with no acceptance handshake.
- `ACK_ONLY`: target becomes active on acceptance; source relinquishes only when its separate quiescence event is processed.
- `TWO_PHASE`: source relinquishes on its quiescence event; target becomes active only after accepted offer plus delivered commit.
- `THREE_PHASE`: target must prepare, source must quiesce, then delivered commit activates target.
- `FAIL_CLOSED_NO_OWNER`: source relinquishes on transfer request and no target may activate.

These minimal, explicit definitions intentionally expose the authority-gap/overlap tradeoff. They do not model leases as permission to exceed the source's pre-existing authority; they model only responsibility ownership.

## Files

- `model.py`: policy transitions and frozen scenario set.
- `run.py`: writes immutable raw event traces and summary.
- `audit.py`: independently recomputes ownership cardinality and summary from raw traces.
- `test_model.py`: construction tests for safety and decision classification.

All outputs are additive to this directory. Preserve any first-run failure unchanged.

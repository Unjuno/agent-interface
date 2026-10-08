# V39 future-done observation backlog A02

This pinned current-main construction test exercises the new completion-time queue drain after the planner future is done. It feeds a synthetic typed health change from 100 to 70 against a hard floor of 80. One case includes the matching completed, verified-empty cover terminal in the drained backlog; the other requires the production cancellation helper to obtain a cancelled terminal. Both pass the retained invalidation to the production final-admission decision.

## H / T / D / C / U

- **H:** The completion-time backlog drain preserves hard policy invalidation and final admission rejects the planner result, whether a matching verified terminal is already queued or must be obtained by cancellation.
- **T:** Execute the pinned `drain_pending_observation_events`, the exact `if future.done() and invalidation is None` AST block, the nested production wait, cancellation/terminal helpers, the adapter, and final-admission-v1 decision with two synthetic queue configurations.
- **D:** Pass only if both cases end `REJECTED_POLICY_INVALIDATED` with no input authority; queued-terminal path verifies closure without redundant cancel, while no-terminal path sends cancel before interrupt transport and waits for verified-empty release.
- **C:** Source-slice construction with synthetic observations and deterministic fakes; no live runner, producer, model, game, GUI, or OS input.
- **U:** No live threat exposure, HUD accuracy/cadence, physical key-state, recovery efficacy, progress, survival, or task outcome.

Source identities are frozen in `FREEZE.json`. Candidate outputs refuse overwrite.

## Reproduction

```text
python -m research.doom.v39_future_done_backlog_a02_20261008.candidate
python -m research.doom.v39_future_done_backlog_a02_20261008.audit
python -m unittest -v research.doom.v39_future_done_backlog_a02_20261008.test_audit
```


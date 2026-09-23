# Temporal-buffer-informed speculative futures — Rung0 first outcome

Decision: `PASS_TEMPORAL_SPECULATION_COMPOSITION_SCOPED`.

One source-first formal invocation; seed `107420260918001`; reruns/replacements/tuning 0.

## Result

With the same current state `0`, the same candidate universe `{-2,-1,+1,+2}`, and the same branch budget `K=2`:

- `CURRENT_ONLY` always prepared `{-1,+1}`;
- `TEMPORAL_INFORMED` used only the preceding three-position history to rank two candidates: monotone-right -> `{+1,+2}`, monotone-left -> `{-1,-2}`, ambiguous -> `{-1,+1}`.

Primary 200,000 cases/arm:
- current-only hit rate: 75.907%;
- temporal-informed hit rate: 83.991%;
- gain: **+8.084 percentage points**.

Dynamic opposite-history subset, 160,000 cases/arm:
- current-only: 69.88375%;
- temporal-informed: 79.98875%;
- gain: **+10.105 percentage points**.

Ambiguous-history 40,000 cases produced the same selection 40,000/40,000 and equal hits 40,000/40,000. All 80,000 same-current/opposite-history pairs kept current-only selection identical while temporal-informed selection was opposite as preregistered.

Safety/epistemic controls remained fail-closed: forced reversal temporal admissions 0/40,000; expiry admissions 0/20,000; no-authority admissions 0/20,000; wrong admissions 0; historical-authority paths 0; model/GUI/task-input/branch-authority-grant counts 0. Candidate/oracle selection/admission mismatches 0.

Independent audit: PASS/errors `[]`. Postformal scientific-source rehash exact. Six copied-result corruptions all reject.

## Interpretation boundary

This is deliberately a small composition result. The benefit comes from a trivial bounded velocity feature over authored synthetic histories; it does **not** establish that a rich temporal buffer/query system is needed. The correct retained lesson is narrower: when the current frame/state aliases histories with different future distributions, history may improve **which no-authority branches are prepared**, while fresh current evidence and ordinary authority/admission remain the only path to execution.

Forced reversal intentionally shows the limitation: temporal preparation can be wrong, and then it must simply fail to match/admit. No real planner gap, application/task correctness, token benefit, live latency, GUI/game execution, or production speculative-execution claim follows.

A later Rung1, if allocated, should first test the same principle on retained temporal evidence with real invalidation/reversal events before adding learned models or larger branch budgets.

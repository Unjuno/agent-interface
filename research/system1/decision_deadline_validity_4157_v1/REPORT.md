# Issue #4157 — explicit decision deadline validity v1

Decision: **PASS_DEADLINE_VALIDITY_SCOPED**.

Formal allocation: one 24-case source-frozen invocation; formal reruns/replacements/exclusions/tuning: **0**.

## H
A task-authored decision deadline can invalidate a local proposal even while observation identity, epoch, ordinary freshness and lease remain valid.

## T
A separate cooperative application process published a static `STATIC_GO` observation, a 120 ms absolute decision deadline, and independent 400 ms lease/freshness bounds in the same `CLOCK_MONOTONIC` domain. Two policies were compared at target proposal delays 20/90/150/260 ms, three repetitions each. No model, GUI, input or network was used.

## D / first outcome
- Frozen raw-only audit: 461 checks, errors=[].
- Currentness-only admitted all 6 late 150/260 ms proposals; all 6 resulting application receipts were independently after the 120 ms semantic deadline.
- Explicit-deadline refused all 6 late proposals with zero effects.
- Both policies admitted all 12 on-time/near-before cases, and all 12 application receipts were independently on-time.
- All proposals remained within the separate 400 ms lease and freshness budgets.
- Action authority remained false.
- 10/10 copied-evidence mutations rejected after intact evidence passed.
- Raw SHA-256: `25383ed1ee8c6fc8a4be2b79f8a1338617e23e499be287065d82696df1898f07`.

## C
This is a deliberately time-semantic fixture, not a claim that every late proposal is unsafe. Proposal-ready deadline semantics may still be insufficient when dispatch/effect latency is itself material. Existing lease/freshness values were deliberately wider than the task decision window to isolate the factor.

## U
No universal latency target, clock-domain translation, hard real-time guarantee, model quality, token saving, OS action, GUI effect, natural failure rate or production default is established. Directed repetitions are finite coverage.

## Retained postformal tooling incident
The first postformal unittest command used `python -I`, which removed the study directory from the module search path and produced `ModuleNotFoundError: test_policy`. This occurred after the formal run and changed no evidence. The unchanged frozen test suite was then invoked read-only without `-I`: 8/8 tests passed. The failure and corrected outputs are both retained.

## Integration meaning
For local delegation, `observation still current` and `proposal still semantically timely for this decision` are distinct predicates in this fixture. A production change should only follow after a real application/model-facing transfer and explicit accounting of proposal→dispatch→effect time.

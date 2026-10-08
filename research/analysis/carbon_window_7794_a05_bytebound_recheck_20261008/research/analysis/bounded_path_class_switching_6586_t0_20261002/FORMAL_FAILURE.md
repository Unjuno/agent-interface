# Retained formal outcome — FAIL_OR_HOLD

- Allocation: `PATH-CLASS-6586-T0-20261002-01`
- Source main SHA: `f1d8f6319ad6a1d6fd7f0219c17bb13f48fae7aa`
- Frozen sources: `FREEZE.json`; freeze SHA-256 `06bda3b5ee687c8671fe33aed6f2c6c412f0420cadad3a1d5bee4d1969eea25a`
- Raw output: `results/a01/raw.json`; SHA-256 `d23bd294f254ef303c1094cbbeb48cbd616cfc74a075d901f0bce262db00b887`
- Independent audit: `results/a01/audit.json`; SHA-256 `ec99acf4a75132468e3c5b65b566b62f378127ed375c5f8700bf3ba3b6ea32ee`
- Host: macOS, Python 3.14.5; not container isolated.

## Observed outcome

The candidate produced all 18 preregistered rows. In `blocked_class_gain`, each policy reached the goal; class-aware recorded 6 observations + 5 input actions = 11 counted events, versus 12 + 11 = 23 for each baseline, with one route-switch backtrack. Controls behaved as intended in the raw row summaries: viable same-class and same-class-dead-end reached goal without class switch; false binding and stale epoch did not switch; single-class yielded `NO_ALTERNATE_CLASS`.

## Gate failure

The frozen independent auditor returned `FAIL_OR_HOLD` with 15 row replay failures: `missing_action_after_observation` for every goal-reaching row. The runner records goal as an `OBSERVE` event and exits on terminal `GOAL_OBSERVED`, but does not append the `STOP_GOAL` action expected by the auditor. The raw therefore cannot establish a complete action-terminated trace under the preregistered independent replay gate. Mutation tests did not run because base validation failed.

## Disposition

Preserve this first formal outcome unchanged. No source repair, result rewrite, or rerun is part of this allocation. The favorable raw cost difference is descriptive only, not a PASS: the independent audit gate failed. Any follow-on should be separately specified and frozen, with an explicit goal-terminal event contract and tests for every terminal path, and should reference rather than replace this evidence. No real topological inference, GUI/DOOM progress, runtime benefit, or container result is claimed.

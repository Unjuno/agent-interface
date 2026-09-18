# #1897 MANIPULATE_TO predicate-support union — preformal stop

Decision: **STOP_PREFORMAL_FULL_CORPUS_CONSUMED_NO_FORMAL**. Scientific disposition: **NONE**.

## What happened

The intended construction was supposed to exercise only a few directed MANIPULATE_TO cases before freezing source. Instead, the exploratory script enumerated the complete frozen-shaped state space:

- phases: PREPARE, EFFECT_PENDING, TERMINAL;
- current predicate states: 16;
- next predicate states: 16;
- total: **768 rows**.

That is the full scientific corpus described by the Issue. The complete result was therefore visible before source freeze.

Running the same 768 rows again after freeze would not be a first formal outcome; it would be a rerun selected after seeing the answer. This Issue therefore stops. No formal invocation is executed.

## Non-poolable exploratory observation

The consumed exploratory output was PASS-shaped:

- presentation-only false suppressions:112;
- phase-support-union false suppressions:0;
- candidate safe suppressions:112;
- candidate false-forwards:178;
- global-all false-forwards:242;
- removing every declared decision-relevant support domain caused at least one false suppression.

These numbers are retained only to explain the stop and inform later question selection. They are **not formal evidence**, are **not poolable**, and must not be relabeled as a PASS.

## Boundary

Do not open a successor merely to rerun this identical 768-row corpus under a source freeze. A successor is justified only for a materially different research question—for example exact state-conditioned minimal support rather than the already-consumed phase-level support-union question.

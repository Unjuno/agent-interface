# Issue #7078 T0 A01 — elective plan-note loss and custody fixture

Status before freeze: construction only. Scope: `T0_METHOD_ONLY`. This CPU-only finite fixture tests authored arithmetic and record-contract checks. It does not observe any model, human, GUI, memory behavior, or product outcome; authored probabilities are not empirical estimates.

## Question and decision rule

For an elective advisory note, does the fixed loss rule select the lower expected loss while preserving mandatory records and rejecting stale, unbound or undelivered notes? Let q0 be an authored forecast of unaided success, q1 the authored success when the note is delivered, L safe rediscovery loss, c forecast/write/read cost, and d delivery probability. The synthetic expected losses are `NO_NOTE=(1-q0)L` and `NOTE=c + d(1-q1)L + (1-d)(1-q0)L`. Strictly lower loss wins; ties choose `NO_NOTE`. This is bookkeeping on authored values only. No probability can waive an authority, effect, evidence, release or ownership obligation.

## Frozen finite cases

Three cases cover a beneficial low-cost note, an expensive note, and unreliable delivery. Every case includes a mandatory unresolved obligation and an advisory source-bound note. The contract requires the mandatory record in every output; note eligibility requires matching source and generation and confirmed delivery. Training/calibration identifiers must be disjoint from held-out identifiers.

## Independent audit

The auditor reads only frozen input, candidate output, and oracle. It independently reconstructs losses and choices and checks record conservation, provenance, delivery, generation and split integrity. It does not import candidate code. Construction mutation tests must demonstrate rejection of mandatory-to-advisory laundering, factual-support substitution for q0, test/calibration leakage, failed-write relabeling, stale-note acceptance and forecast-cost erasure.

## Disposition limits

Even a full scoped pass establishes only that this finite contract and arithmetic fixture behaved as specified under its authored values. It says nothing about q0 calibration, model continuation, actual note cost, or user benefit. Any candidate/auditor invocation failure is preserved as the first outcome and is not retried under A01.

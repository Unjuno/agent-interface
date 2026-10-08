# Issue #6086 T0 — hazard-shaped discretionary capture

## Disposition

`FAIL_METHOD` on the frozen threshold: at cue width 1/2, hazard detection was 16/73, uniform 10/73, and phase-diversified 9/73. Its gains (6/73 and 7/73) are below the predeclared 1/10 absolute improvement gate. At width 1 the hazard score was 63/146 versus 39/146 and 37/146, meeting that component of the gate, but the rule required both widths. Flat weights tied at both widths; the inverted distribution penalized hazard concentration. No threshold or schedule was changed after execution.

The independent auditor also reported `candidate_oracle_mismatch`. The auditor compared whole output rows, including candidate-only mean-delay fields; it did not retain the oracle rows separately, so the exact score cross-check cannot be reconstructed from the retained raw output. This is an audit-artifact failure, not evidence that the numeric rows disagree. No PASS is claimed, and no retry or output normalization was performed.

## Deviation from the full Issue T0

The frozen minimal probe was incomplete relative to the Issue's required T0 matrix. It omitted explicit imperfect-detection/exposure control, false-positive accounting, worst-onset and max-gap scoring, no-cue data row, rejected scored-label leakage policy, zero/unknown-hazard control, and the all-budget-mandatory `NOT_APPLICABLE` control. Therefore this is a partial diagnostic, not completion of the Issue's T0. These omissions remain open; they are not inferred to pass from absent data.

## H / T / D / C / U

Frozen parameters and gates are in `PLAN.md` and `freeze.json`. All schedules had three discretionary exposures plus the same separate sentinels at 0, 6, and 12. The miss semantics never upgraded a missed cue to absence or safety. The synthetic score does not support live cue capture, a calibrated hazard model, mandatory coverage changes, safety, or task benefit.

## Execution boundary

One local Python 3.12.10 auditor invocation launched one candidate and one integer half-tick exhaustive oracle. No model, GUI, input, or external allocation was used. Docker Desktop's server-version query on the `desktop-linux` context remained unresponsive in this environment; this result is not a container run. First result retained without retry.

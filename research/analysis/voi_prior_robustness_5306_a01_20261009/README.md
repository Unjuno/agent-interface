# VOI prior-set robustness — A01 result

## Outcome

**`PASS_METHOD_SCOPED` diagnostic; Issue-level HOLD.** On the point case, point VOI and the fixed-margin comparator both choose STOP at `p=9/10` (net value zero, ties stop). The frozen set `{22/25, 9/10, 47/50}` contains a CONTINUE point (`1/5` net) and STOP points (`0`, `-2/5`), so the prior-set label is `PRIOR_SENSITIVE`. The robust STOP, robust CONTINUE, correlated-duplicate, deadline-infeasible, and mandatory-incomplete controls all receive their preregistered dispositions.

The independent exact-rational auditor recomputed all six rows with zero errors. The seven construction tests pass both normally and under `-O`. The retained candidate and auditor records are `results/candidate.raw.json` and `results/audit.raw.json`; `RUN.json` and `SHA256SUMS` record invocation status and identities.

## Decision and limits

This shows that a point-VOI label can hide a decision reversal within a declared finite prior set, while robust controls remain decidable and hard gates still yield. It is an exact result for authored fixture values. `P` and utility weights were selected to probe the mathematical boundary; they are not evidence-supported estimates. There is no independent held-out outcome cohort, probability-coverage result, or empirical verifier data. Therefore this does **not** satisfy #5306's broader evidence-backed hypothesis and is not a policy recommendation.

No latency, seconds, tokens, monetary cost, GUI behavior, task effect, or product safety was measured. Utility values are dimensionless fixture weights. A separate empirical calibration/coverage study and an actual task-effect oracle are still required before any operational VOI stopping claim.

## Run integrity note

The candidate command ran once and wrote a complete raw JSON file. Its shell pipeline returned 1 because `tee` tried to open `results/candidate.stdout.txt` before the candidate created `results/`. The complete JSON remained visible in the tool output, and the source's completed print path returns 0; the standalone process exit was not separately captured. The saved raw file was independently audited once. No candidate retry occurred. This capture-wrapper discrepancy is preserved in `results/CAPTURE_NOTE.txt` and `RUN.json`.

The experiment ran on macOS 27.0 arm64 with CPython 3.14.5 and only the standard library. It used no container/shared daemon, model, GUI, or live application.

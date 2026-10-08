# Retained construction failures (do not overwrite)

## Attempt 01 — unreachable synthetic counterexamples

The first frozen graph omitted routes from `loop1`, `loop2`, and `wrong` to
the goal-connected component. The candidate returned `UNKNOWN` for these
states, and the independent expected-class check returned
`FAIL_CONSTRUCTION` (coverage-only and wrong-direction class-sequence
mismatches). This was a defect in the synthetic fixture, not evidence about
MAP01. It was superseded by the explicit fixture revision in `run.py`; the
failed decision is retained here rather than silently relabeled.

## Attempt 02 — coverage loop contained directed regressions

The first fixture repair connected only `loop2` to the goal-connected
component. The candidate then returned
`NO_BASELINE, REGRESSION, USEFUL_PROGRESS, REGRESSION` for the loop and the
independent expected-class check still returned `FAIL_CONSTRUCTION`. The
fixture was revised to make both loop states have equal shortest-path
distance to the goal. No observed sequence was dropped from this record.

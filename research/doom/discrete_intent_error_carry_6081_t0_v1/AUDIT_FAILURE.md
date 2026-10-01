# First T0 audit failure — preserved

Disposition: `FAIL_UNSAFE_SCHEDULE`.

The candidate and the independent oracle agreed on all 40 serialized policy rows. The auditor then stopped at the frozen safety-envelope assertion (line 48) before computing the win tally or running its mutation controls.

Raw witness: `exact-east`, four `E` slots from x=0 produce x-prefixes `[1, 2, 3, 4]`; the frozen safety box has `xmax=3`. A, B, and C each report one violation, and all incorrectly remain `SCHEDULED`. The omission is in candidate safety handling, not a reason to weaken the frozen box.

Candidate invocation: one, exit 0. Auditor invocation: one, exit 1. Retries: zero. Neither is rerun. This is a synthetic candidate failure; no live control was executed.

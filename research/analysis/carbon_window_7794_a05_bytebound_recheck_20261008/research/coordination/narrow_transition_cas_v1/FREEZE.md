# Narrow transition CAS freeze

Task `COORD-NARROW-TRANSITION-CAS-20260916-017`, Issue #487.

No measured update has executed at this freeze. Publication base is `defb76363803ac76875924b7246de76a1f6d6963`.

Single factor: CAS footprint width.

Frozen order:
1. wide_unrelated
2. narrow_unrelated
3. narrow_membership
4. narrow_stable

Measured GitHub writes use the exact initial blob SHA captured before intervention. No fresh-SHA retry, merge recovery, alternate token, second read between validation and measured commit, or post-result tuning.

Decision is `PASS_NARROW_TRANSITION_CAS_SCOPED` only when the gates in Issue #487 and `plan.json` all hold.

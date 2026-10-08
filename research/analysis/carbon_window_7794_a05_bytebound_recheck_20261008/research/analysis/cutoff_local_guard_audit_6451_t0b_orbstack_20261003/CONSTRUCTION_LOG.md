# Construction log — pre-formal failures and corrections

This file preserves construction-stage discrepancies. None consumed a formal candidate or auditor invocation.

## Attempt 01 — incorrect test oracle expectation

Command: `python3 -B -m unittest discover -s research/analysis/cutoff_local_guard_audit_6451_t0b_orbstack_20261003 -p 'test_*.py' -v`

Result: 4/5 passed. `test_comparator_is_strictly_restricted_to_frozen_bandwidth` expected the symmetric within-bandwidth outcome mean difference to equal the planted treatment effect (2), but observed 11. This is not a candidate defect: the mean difference intentionally retains the smooth outcome-age trend (9) plus treatment effect (2), while the local-linear RD estimator removes that smooth trend and returns 2. The frozen comparison requires these estimands to remain distinct. Correction: change only the construction assertion to expect 11 for the naive band-limited contrast and assert 2 for the local-linear effect; no protocol, candidate, auditor, fixture, or formal gate changed. The original #6451 consumed allocation and its source/raw status were untouched.

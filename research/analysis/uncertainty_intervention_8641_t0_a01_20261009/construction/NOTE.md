# Construction attempts

The first construction output at `construction/candidate.json` with `construction/audit.json` is retained as the initial smoke attempt. Its audit incorrectly classified the scientific H-gate misses as audit errors; this was corrected before formal freeze. The candidate and audit sources were then separated into a clean integrity disposition and an H disposition.

`attempt_02/` is the corrected 20-seed disjoint construction. Independent reconstruction passed 480 rows with zero audit errors; the hypothesis result was `H_FAIL_NO_ADDED_DECISION_VALUE`. The source-dependence, stale-epoch action, and cost mutation controls each failed the audit as expected (4/4). These are construction-only rows and are not pooled with the formal allocation.

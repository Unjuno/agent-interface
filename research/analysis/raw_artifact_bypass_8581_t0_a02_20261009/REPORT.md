# Issue #8581 T0 A02 — first outcome retained

**Disposition: `HOLD_ACCESS_OR_AUDIT`.** The candidate ran once and emitted 4 cells / 92 events. The independent auditor's JSON reports eight discrepancies between candidate output and its reconstructed selection/events, while rejecting all five frozen mutations. It then exited 1 because the final stdout summary referenced a removed local variable; the JSON report and exact traceback are retained.

Read-only diagnosis found the reconstruction mismatch: the candidate generated labels with `Random.randrange(2)`, while the auditor generated them with `Random.getrandbits(1)`. These calls consume randomness differently in the pinned runtime. The first candidate and audit were not rerun. No scientific comparison is assigned.

A corrected successor must use a distinct allocation and new seed. A01's original auditor failure and A02's first output/audit remain immutable; no data are pooled. Scope is the authored synthetic fixture only, with no claim about researcher behavior or real artifact access.

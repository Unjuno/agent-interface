# Issue #8581 T0 A01 — first outcome retained

**Disposition: `HOLD_AUDITOR_FAILURE`.** The frozen candidate ran once and emitted all four preregistered cells and 88 events with exit code 0. The independent auditor ran once but exited 1 before producing an audit because its mutation-control loop passed a boolean into the raw-output validator. The exact exception and candidate output are retained. No candidate or auditor retry was performed, and no scientific comparison is assigned.

The failure is in the independent audit harness; it does not establish whether controlled feedback limits adaptive overfit or whether a raw artifact bypass defeats it. A corrected successor requires a distinct allocation, new source freeze, and new candidate data. A01 stays immutable.

Scope remains the authored deterministic fixture only. This result says nothing about researcher behavior, real evaluation-artifact access, historical repository results, or unknown channels. Exact safety vetoes were part of the attempted fixture but their acceptance has not been formally audited.

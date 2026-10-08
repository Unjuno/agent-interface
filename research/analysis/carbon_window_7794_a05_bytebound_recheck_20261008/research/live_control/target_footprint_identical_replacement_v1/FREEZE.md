# Source-first measurement freeze

Task: `FOOTPRINT-IDENTICAL-REPLACEMENT-20260916-001`, Issue #347.
Publication BASE: `4e802fa2ec3c0c97545a38520bb18b3b126d8e4e`.
No scored/formal case has run at publication of this freeze.

The exact upstream `target_footprint_reacquire_v1/resolver.py` snapshot is retained byte-for-byte as `upstream_resolver.py`; its Git blob identity must be `a8bb0e564bae738c9091b737ff2abe1922520ec1`.

Construction only, excluded from measurement: two pairs used the exact candidate runner in `--construction` mode. In both, stable and replacement current PNG/RGB were identical; both arms resolved `UNIQUE` at the same translated point. This established fixture viability only and did not change thresholds, radius, template size, case count or decision gates.

Formal allocation: eight matched pairs / sixteen current arms. Each pair has one reference `target-A`; stable current retains `target-A`, replacement current substitutes `replacement-X`. Stable and replacement use identical rendered geometry/style and the same translation. Inkscape CLI renders each case separately at 600x400. The resolver receives only pixels, reference footprint and source prediction; XML object IDs are independent evaluator-only evidence.

Hard gates are exactly those in `prereg.json`. Any pair whose stable/replacement current RGB pixels differ is setup failure, not evidence for or against identity. Stable must resolve `UNIQUE` at the exact translated center. Replacement must have `target-A` absent and `replacement-X` present, while producing decision-relevant resolver evidence identical to stable. If every gate passes, decision is `RETAIN_IDENTICAL_REPLACEMENT_BOUNDARY`. No consequential task input occurs in this rung.

One formal output directory, first outcomes only. No rerun, replacement, extension, threshold/radius/template tuning or success-seeking repair after the first formal case. Offline audit and corruption tests may consume retained formal bytes only; they may not execute another measurement block.

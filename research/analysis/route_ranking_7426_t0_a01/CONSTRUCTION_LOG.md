# Construction log

The first candidate run exposed a missing conventional-aggregate lookup for controlled singleton-axis fixtures; the selector was changed to return `null` when the equal/equal point is outside that fixture's declared domain. This changed only report availability, not scoring.

The first audit mutation assertion compared only the coarse `MIXED_OR_TIED_REGION` label; a preregistered latency mutation changed exact winner counts without changing that label. The check was strengthened to compare the complete region counts, as required by “change, narrow, or remain HOLD.”

A later report-boundary assertion initially carried partial winners for the 343 fully-scored mix/weight pairs in the missing-data fixture. The final independent audit suppresses all partial winner counts whenever any admissible pair is incomplete and reports the 343 complete and 441 incomplete pairs separately. The disposition remains HOLD. The candidate itself already returned HOLD and did not promote those partial counts as a winner region.

Only synthetic construction scripts and their retained outputs were run. No live or formal allocation was consumed.

# Issue #8597 T0 A01 — tail-regret ranking sensitivity

**Disposition: `PASS_METHOD_SCOPED`.** The fixed synthetic fixture demonstrates the preregistered finite ranking reversal, and the raw-only auditor reconstructed every row and all six corruption controls. It does not establish that any real GUI route has a heavy-tailed loss distribution or that a tail metric should control route selection.

## Result

Across 24 fully observed, assigned synthetic decision opportunities in two strata and six four-opportunity session clusters, routes A and B each had pooled mean regret 0.5 synthetic units. ES20, defined before execution as the mean of the largest `ceil(0.20 × n)` opportunity losses (top five of 24), was 2.2 for A and 1.0 for B. The equal mean therefore concealed a finite tail-rank difference in this authored fixture.

The difference persists in S1: each route's mean is 1.0, while S1 ES20 is 8/3 for A and 1.0 for B. S2 has mean and ES20 zero for both routes. Macro mean is 0.5 for both routes; macro ES20 is 4/3 for A and 0.5 for B. The primary exceedance count at loss ≥3 is A 2/24 and B 0/24. Route C is an all-zero finite control.

The six cluster means and delete-one-cluster pooled-mean ranges are recorded in `audit.json`. The A range [0.1,0.6] and B range [0.4,0.6] overlap, illustrating that the small finite fixture does not support a robust route winner. This deletion range is descriptive only and has no calibrated coverage.

The independent auditor reported 24 assigned opportunities, 288 route/tick rows, zero audit errors, six of six rejected mutations, and zero hard-safety events in the ranked cohort. A separate planted hard-safety control remains `FAIL_HARD_SAFETY` with a null numeric value. The benign score spike (1000) is `OUT_OF_SCOPE_BENIGN` and excluded; missing truth remains `UNKNOWN`; censored follow-up remains `UNRESOLVED_CENSORED`. None is silently assigned zero or pooled.

## Method and custody

The source freeze is commit `43c730b9192cf972453454335248d50d29ab093c`, based on current main `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`. GitHub readback matched all 10 frozen source/input blobs before execution. The semantic reference is Issue #8528 result commit `3f6bc41adaaf6dcc96ff0fd0deea5c691140c8d8`; its finite 0/1 open-tick mismatch loss and admissible-action comparator informed the per-opportunity endpoint. This A01 uses a separately authored action/target fixture and does not rerun or modify #8528.

The candidate ran once and emitted 288 rows. The independent auditor ran once from the saved candidate raw and audit-only truth, reconstructed the per-opportunity losses, denominators, summaries, and mutation controls without importing candidate code. Exact stdout, timestamps, exit codes, raw, audit, freeze, and SHA-256 manifest are retained in this directory. No retries occurred. Python 3.14.5 on Darwin ARM64 host CPU; standard library only. No model, GUI, human, external service, runtime, Docker/WSL container, or GPU was used because the finite calculation does not depend on those systems.

## Limits

This establishes only that the predeclared ES20 statistic distinguishes these authored finite cases while preserving their declared strata and categorical controls. It does not estimate population CVaR, calibrate confidence, identify real route quality, justify thresholds or runtime decisions, establish causality, measure human value, or prove safety. Opportunities are deliberately clustered and heterogeneous; six clusters are too few for inferential calibration. Loss values and the ES20 level are fixture conventions.

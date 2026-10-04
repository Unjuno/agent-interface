# T5 audit-classification review — Issue #5156

## H / T / D / C / U

- **H:** The T4 raw rows remain classifiable if readiness mismatches are partitioned by the frozen oracle: a negative control being ready is a timestamp-order acceptance; a positive control being not-ready is a positive-control failure. These are distinct scientific outcomes.
- **T:** Do not invoke the candidate or T4 auditor again. Read the immutable T4 `cases.json` and `output/raw.json`; run this review-only classifier once, after tests cover all four positive/negative mismatch combinations. Keep T4 files and conclusions unchanged.
- **D:** Integrity validation is inherited from T4's raw-only `classify`. With valid raw, report `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED` only for mismatches on expected-not-ready cases; report `FAIL_POSITIVE_CONTROL` only for mismatches on expected-ready cases; report both distinctly if both occur; otherwise `PASS_ORDER_GATE_SCOPED`.
- **C:** Host Python standard library only. No container was launched because the observed OrbStack content-store failure remains unresolved. No runtime, X11, game, input device, model, provider, or GPU is used.
- **U:** Whether T4's saved synthetic output passes a classification that preserves positive- and negative-control meaning. This review cannot establish live owner-thread timestamps or close Issue #5156/#59.

T4's saved raw is the sole input. T5 is an additive review artifact; it does not alter T4's frozen evidence or count as a new candidate experiment.

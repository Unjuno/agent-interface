# T5 audit-classification review — Issue #5156

## H / T / D / C / U

- **H:** The T4 raw rows remain classifiable if readiness mismatches are partitioned by the frozen oracle: a negative control being ready is a timestamp-order acceptance; a positive control being not-ready is a positive-control failure. These are distinct scientific outcomes.
- **T:** Do not invoke the candidate or T4 auditor again. Read the immutable T4 `cases.json` and `output/raw.json`; reconstruct expected event rows and analyzer outputs from the frozen source, test all four positive/negative mismatch combinations and the four independently reported raw mutations, then run this review-only audit once. Keep T4 files and conclusions unchanged.
- **D:** Require exact equality of every retained row (case ID, full event array, and full analyzer output) to a reconstruction from frozen cases and source. Reject any mismatch as `STOP_RAW_INTEGRITY`. With integrity-valid raw, report `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED` only for mismatches on expected-not-ready cases; report `FAIL_POSITIVE_CONTROL` only for mismatches on expected-ready cases; report both distinctly if both occur; otherwise `PASS_ORDER_GATE_SCOPED`.
- **C:** Host Python standard library only. No container was launched because the observed OrbStack content-store failure remains unresolved. No runtime, X11, game, input device, model, provider, or GPU is used.
- **U:** Whether T4's saved synthetic output passes a classification that preserves positive- and negative-control meaning. This review cannot establish live owner-thread timestamps or close Issue #5156/#59.

T4's saved raw is the sole input. T5 is an additive review artifact; it does not alter T4's frozen evidence or count as a new candidate experiment.

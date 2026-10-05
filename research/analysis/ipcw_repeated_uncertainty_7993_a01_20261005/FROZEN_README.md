# Issue #8049 — repeated-cohort IPCW uncertainty A01

**Status: construction only; formal allocation not yet run.** This additive package tests repeated-sample uncertainty under one known synthetic design. It is not a live verifier calibration or completion of Issue #7993.

## H / T / D / C / U

### H — hypothesis

Under the previously declared two-stratum design, the uncapped stratified Horvitz–Thompson (HT) estimator is unbiased for marginal expected risk but more variable than complete-case risk. A nominal 95% stratified Wald interval using the candidate-visible per-unit weighted contributions may achieve 94.4–95.6% empirical coverage across 20,000 independent cohorts. A nominal complete-case Wald interval is not expected to cover the marginal 0.25 risk because resolution rates differ by stratum and error prevalence differs by stratum.

### T — frozen protocol

- Fixed cohort size 400: exactly 200 independent units in each stratum A and B.
- Outcomes: independent Bernoulli with p(A)=0.40 and p(B)=0.10; target marginal expected risk is exactly 0.25.
- Independent resolution: q(A)=0.25 and q(B)=0.75, independent of outcome within each stratum.
- Seed 8049001; 20,000 independent cohorts. Generator, config and fixture inputs are source-hashed before formal execution.
- Candidate receives only resolution bitmasks and resolved-outcome bitmasks. Oracle outcomes are held in a separate file mounted for the auditor only.
- For each stratum h, candidate HT contribution is Z_i=Delta_i*Y_i/q_h, with unresolved contribution zero. Candidate reports HT=(sum_h sum_i Z_i)/400 and estimated variance sum_h(200*s_h^2)/400^2, where s_h^2 is the sample variance of the 200 known Z_i values in that stratum. A 95% Wald interval is HT ± 1.959963984540054*SE, clipped to [0,1].
- Complete-case comparator is total resolved errors / total resolved labels, with ordinary binomial Wald interval clipped to [0,1]. It is diagnostic only.
- Exact HT design variance is [p_A/q_A-p_A^2 + p_B/q_B-p_B^2]/(2*400). Monte Carlo decision gates: HT mean within 4 exact Monte Carlo standard errors of 0.25; HT sample SD within 2.5% of the exact SD; HT interval coverage within 0.006 of 0.95; and complete-case coverage recorded (failure to cover is informative, not by itself a failed software implementation).
- One formal, no-retry candidate+auditor invocation in the locally available digest-pinned OrbStack container, `--network none`, one CPU, read-only source, separate writable output. Container resource flags do not prove memory enforcement.

### D — disposition

`PASS_METHOD_SCOPED` only if input/source hashes reconcile, all 20,000 cohorts and all 400 identities per cohort are independently reconstructed, output estimates and intervals match the raw-only auditor, exact risk/variance formulae reconcile, preregistered HT mean/SD/coverage tolerances pass, and frozen mutations are rejected. Any preregistered Monte Carlo gate miss is `FAIL_METHOD` for the corresponding interval claim, while preserving all raw evidence. `HOLD` on incomplete cohorts, identity mismatch, candidate/oracle leakage, ambiguous invocation receipt, or independent-audit failure.

No interval is a distribution-free, shift-robust, finite-cohort guarantee. The HT interval is evaluated only under the exact known model above; the complete-case result is not generalized beyond this authored design.

### C — alternatives

The finite-cohort all-assigned interval from #8028 makes no censor-model assumption but may remain wide. The exact expectation subgate from #8045 proves neither sample variance estimation nor interval coverage. The exploratory #8034 Monte Carlo reports means and SD but has no frozen candidate/auditor separation or interval gate.

### U — limits

One Bernoulli population, one fixed stratification, known propensities, one seed and one interval recipe. No estimated censoring, model misspecification, distribution shift, real verifier labels, GUI, product effect, safety or action authority.

## Reproduction

Construction: `python3 generate.py`, `python3 -m unittest -v test_protocol.py`.
Formal container command and raw receipts will be added only after the freeze; the one-shot formal driver is `run_formal.py`.

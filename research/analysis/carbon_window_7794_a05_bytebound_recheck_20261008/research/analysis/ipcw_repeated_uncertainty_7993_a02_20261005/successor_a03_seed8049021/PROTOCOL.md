# Issue #8049 — A03 fresh-seed bootstrap coverage allocation

## H / T / D / C / U

**H.** Under the exact two-stratum independent-outcome/independent-resolution model, the conditional stratified percentile-bootstrap interval over observed HT contributions will meet the preregistered 95% repeated-cohort coverage tolerance on a new seed. A02's CLI STOP is execution infrastructure only; it is not a method failure and is not retried.

**T.** New allocation `UNJUNO-8049-IPCW-REPEATED-UNCERTAINTY-A03-ORBSTACK-20261005`, seed `8049021`, 20,000 cohorts, 200 units/stratum, risks `(0.40, 0.10)`, independent response probabilities `(0.25, 0.75)`, target risk `0.25`. Reuse the byte-identical A02 candidate and independent auditor sources by hash-bound relative reference; generate new public/oracle fixtures from this fresh seed. The interval is the exact conditional percentile bootstrap over fixed-size within-stratum resamples of observed IPW contributions. Integer numerator is `3*K_A+K_B` over denominator 300; quantiles are the first cumulative masses at `0.025000000001` and `0.975000000001`, clipped to `[0,300]`. Candidate sees public masks only; auditor also sees oracle outcomes. Candidate and auditor run once in separate containers, zero retries.

Before freeze, a non-candidate no-network mount smoke on the same pinned image must read a file through a read-only bind and write a marker through the default read-write bind syntax. Formal runner omits a bare `rw` field. Image: `python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151`; `--pull=never`, `--network=none`, read-only rootfs/source, one requested CPU, requested 1 GiB, dropped capabilities, `no-new-privileges`, separate outputs and bounded `/tmp`. Memory enforcement is not asserted.

**D.** `PASS_METHOD_SCOPED` only if freeze and both input hashes verify, candidate/auditor each exit 0 once, all 20,000 cohorts/8,000,000 units reconstruct, integer estimates/endpoints match exactly, HT mean is within four exact MCSE of 0.25, empirical HT SD is within 2.5% of exact design SD, bootstrap coverage is within 0.006 of 0.95, and every frozen mutation is rejected. Preserve the first typed FAIL/HOLD/STOP; no retry.

**C.** A01's normal/Wald interval undercovered. A02's STOP never executed either process. Four earlier bootstrap pilots were construction-only; this new seed is required. Bootstrap coverage can differ under misspecification, other propensities, or shift.

**U.** One finite synthetic population and one interval recipe/seed only. No production verifier calibration, distribution-free coverage, GUI/runtime behavior, safety, or action authority claim.

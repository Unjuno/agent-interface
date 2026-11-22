# Formal result — Issue #8049 repeated-cohort IPCW uncertainty A01

## Disposition

**`FAIL_METHOD` for the preregistered 95% stratified HT Wald-interval coverage gate.** The only frozen formal allocation started once, ran the candidate once and auditor once, and used zero retries. Candidate exited 0. The frozen auditor exited 1 at cohort 15 because a strict exact-float dictionary comparison found a one-ULP `ht_se` difference (`0.04442322218052239` versus `0.04442322218052238`). The original failure, stderr, start marker, candidate output, terminal receipt, and frozen manifest are retained unchanged under `out/`. The runner records `audit_sha256: null` because the frozen auditor did not produce its audit artifact.

That raw-audit mismatch is a validation defect, but an explicitly separate post-hoc diagnostic was run against the immutable candidate output and oracle fixture. It reconstructed all 20,000 cohorts / 8,000,000 unit identities and found zero fields outside absolute tolerance `1e-15`. This diagnostic does **not** replace or relabel the frozen auditor exit.

The root README was updated after the run to display its outcome. Its exact preregistration bytes are preserved as `FROZEN_README.md`; that file's SHA-256 equals the frozen manifest's original `README.md` hash. All formal source/input identities remain listed in `FROZEN.json`.

## Preregistered metrics from post-hoc raw reconstruction

- True superpopulation risk: `0.25`.
- Exact HT variance / SD under fixed 200+200 stratum allocation: `0.0019541666666666666` / `0.04420595736624948`.
- HT mean: `0.25023116666666667`, inside the preregistered four-MCSE tolerance `±0.0012503332889007366`.
- HT empirical SD: `0.044535412362996726`, +0.75% versus the exact SD, inside the ±2.5% gate.
- Nominal 95% HT Wald interval coverage: `0.94025`, below the preregistered lower limit `0.944`; the interval gate fails.
- Complete-case mean: `0.1749384642282789`, near its known large-sample limit `0.175`; nominal interval coverage of the true `0.25` risk was `0.21555` in this authored design.

The preregistered decision required HT coverage within ±0.006 of 0.95; mean and SD gates pass, but coverage fails. Thus unbiasedness and accurate standard deviation did not make this specific Wald interval attain its stated 95% target at the registered tolerance. Any alternative interval requires a new prospective protocol/allocation; this run is not to be repeated or repaired in place.

## Execution and limits

OrbStack Docker 29.4.0, `python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151`, Linux arm64, `--network none`, one CPU, requested 1 GiB memory, read-only `/src`, separate writable `/out`. The runtime accepted the memory flag, but effective memory enforcement is not claimed. Candidate input and oracle truth were separate packed fixtures. Seed 8049001, 20,000 cohorts, 400 units each.

The result is limited to one Bernoulli population, fixed strata, known propensities, one seed, and one Wald interval recipe. It is not a distribution-free, shift-robust, finite-cohort, production-verifier, GUI, product-effect, safety, or action-authority result. #7993 remains open.

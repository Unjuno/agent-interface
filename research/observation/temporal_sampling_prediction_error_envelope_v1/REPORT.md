# Temporal sampling prediction-error envelope — formal result

Task `TEMPORAL-SAMPLING-PREDICTION-ERROR-ENVELOPE-20260918-001`, Issue #1497.

## Decision

**`PASS_TEMPORAL_PREDICTION_ERROR_ENVELOPE_SCOPED`**

This is a synthetic timestamp-geometry result over the already frozen INDEX_LOG and TARGET_AGE_LOG samplers. It does not rerun or relabel #752/#808/#804 and it does not establish a frontier-model or live-control benefit.

## What changed

The failed blanket promotion question from #808/#804 is replaced by an explicit conditional guarantee. The shared timestamp-aware OLS linear predictor is evaluated under a caller-declared fixture class: constant acceleration bounded by `A_max`, observation error bounded by `q_max=0.5px`, current time 0 and prediction horizon 100ms. For each six-sample timestamp design, the candidate computes a worst-case latent future-position error bound from timestamps only. `MIN_BOUND` selects the frozen sampler with the lower bound; it never looks at the realized future.

## First formal outcome

Exactly one frozen formal invocation used seed `149720260918001`.

- supported quadratic/cadence cases: **120,000**;
- acceleration-envelope levels: 0/200/500/1000/2000 px/s^2, **24,000 each**;
- six cadence families: **20,000 each**;
- MIN_BOUND choices: **66,066 INDEX_LOG / 53,934 TARGET_AGE_LOG**;
- INDEX bound escapes: **0**;
- TARGET bound escapes: **0**;
- candidate/independent-oracle mismatch: **0**;
- MIN_BOUND-not-min violations: **0**;
- provenance/role violations: **0**;
- clean affine controls: **6,000**, maximum residual `9.592326932761353e-14 px`;
- abrupt-regime-change controls: **10,000/10,000 refused as `UNSUPPORTED_MOTION_CLASS`** with no guarantee or authority.

The maximum candidate/oracle numeric difference was `5.684341886080802e-14`. The closest supported realized errors still remained below their fixed-arm bounds: maximum `(error-bound)` was `-0.14236782178236318px` for INDEX and `-0.13969647628166926px` for TARGET.

Formal row digest: `70ce29599705c4c1dca6d68379d9534cfdae388a06d1d172945fd14b390077cc`.

## Important negative/limiting observation

`MIN_BOUND` is **not** an empirical-error oracle. Across the same 120,000 supported cases, the lower-bound arm had lower realized error in 63,617 cases, tied in 43,209, and had **higher realized error in 13,174**. This is expected and retained: the mechanism minimizes a worst-case guarantee under a declared envelope; it does not claim to identify the realized-error winner.

Therefore the scoped result supports **conditional risk bounding**, not a new claim that TARGET_AGE_LOG or MIN_BOUND is universally more accurate.

## Construction and audit

Before freeze, 36 excluded timestamp designs exercised both choices (25 INDEX / 11 TARGET). Exhaustive acceleration-endpoint × all `2^6` observation-error-sign combinations matched the analytic bound to at most `8.881784197001252e-16px`. A 30,000-row nonformal preflight had 16,521 INDEX / 13,479 TARGET choices, zero bound escapes and zero oracle mismatches.

The frozen independent audit regenerated the full 120,000-row supported corpus plus controls and returned `PASS`, `errors=[]` in 10.19s. The formal run took 10.69s. Environment: Python 3.13.5, AMD EPYC 9V74, 5 vCPU under KVM; these timings are descriptive wrapper measurements, not benchmark thresholds.

The original frozen `corruption.py` invokes a full 120,000-row audit separately for every mutation. The external command wrapper timed out after the audit had already passed; this did **not** rerun the formal allocation. A separately retained postformal driver cached one exact expected regeneration and passed six mutations through the exact frozen `audit.audit` function. It rejected 6/6 corruptions: digest, choice count, bound escape, unsupported count, formal-invocation count and affine residual. Scientific source bytes remained unchanged.

Postformal source rehash matched all nine frozen source members exactly.

## Interpretation

The evidence supports a narrower replacement for blanket temporal-sampler promotion:

- a sampler can expose a worst-case prediction-error guarantee only for an explicitly declared motion/noise class;
- the lower guarantee can switch between INDEX_LOG and TARGET_AGE_LOG as cadence geometry and acceleration envelope change;
- abrupt regime change is outside this guarantee and must YIELD rather than laundering old history into a current guarantee;
- historical temporal samples remain context/evidence only and do not grant current or input authority.

This addresses #804's requested applicability-envelope question without tuning the old age targets. It does **not** yet justify #746 frontier-model Rung1 by itself: a frontier model is not the OLS predictor, and real motion-class membership is not inferred here.

## Evidence limits

Synthetic 1-D constant-acceleration motion, bounded independent observation error, one linear predictor and six-sample policies only. No model, image understanding, real capture, token, latency, task action, GUI, MAP01, human-tempo, reliability-rate or production-ABI claim follows.

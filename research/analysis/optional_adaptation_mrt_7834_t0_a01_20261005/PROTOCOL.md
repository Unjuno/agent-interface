# Issue #7834 T0 A01 — frozen finite-method protocol

## H / T / D / C / U

**H.** In this finite longitudinal model, a known-propensity, availability-aware excursion estimator recovers the oracle marginal proximal effect across all supported pre-assignment histories more accurately than (i) an unweighted/history-ignorant assignment contrast that assumes away history/carryover and (ii) an executed-only contrast under state-dependent nonexecution. Support, timing, missingness, interference, and proximal/distal separation controls must fail closed.

**T.** Enumerate every assignment path for two independent session clusters over four decision points. Availability is computed from pre-assignment history: point 0 always eligible; point 1 eligible iff point-0 assignment was 0; point 2 always eligible; point 3 eligible iff point-2 assignment was 0. The point-0 propensity is 0.5; later propensities are 0.25 or 0.75 according to the recorded point-0 history. Potential proximal outcome includes current execution and a finite three-lag carryover kernel with weight 0.10 per earlier executed action. Assignment is non-executed in one latent session stratum. Estimate the marginal excursion effect and its predeclared `prior execution absent/present` strata. The path-level distal endpoint is separately retained and intentionally need not agree with the proximal endpoint. Enumerate exactly; no Monte Carlo sampling or seed-based uncertainty claim.

Before the sole formal candidate call, hash-bind this protocol, fixture, candidate, construction test, and auditor in `FREEZE.json`. Candidate writes one immutable raw JSON result. A separately implemented raw-only auditor reconstructs all paths, probabilities, potential outcomes, estimands, hard-gate invariants, and five corruption/identifiability controls. No model, GUI, user data, authority, or external effect.

**D.** `PASS_METHOD_SCOPED` only if the independently recomputed IPW excursion effect equals the finite oracle within `1e-12`, both predeclared carryover-history strata separately equal their oracle effects, both naive baselines miss the aggregate oracle by more than the tolerance, mandatory-control snapshots are identical with zero authority additions, all five controls (zero support, post-assignment eligibility, missing proximal window, cross-session interference, and proximal/distal inversion) are correctly rejected, flagged, or kept separate, and raw/source hashes reconcile. Otherwise report the exact FAIL/HOLD without rerunning the formal candidate.

**C.** Episode-level randomization can be simpler; the availability-aware within-session method may add no value when propensities are constant, carryover is absent, or execution is complete. The deterministic authored outcome law may favor this estimator and does not establish calibration for real interfaces.

**U.** Two clusters and four decision points only; no statistical population inference, live treatment effect, user adaptation, GUI correctness, actual task success, latency benefit, or deployment claim. The distal endpoint is synthetic and not a surrogate validation. `PASS_METHOD_SCOPED` is only exact reconstruction of this finite model.

## Execution/environment decision

Base is current main `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`. The issue is an offline standard-library CPU method model. OrbStack Engine API responds, but both image inventory and pulling `python:3.12-slim` fail with containerd `operation not supported` for missing content blobs; no daemon restart, repair, image deletion, or shared-runtime mutation was attempted. No other container runtime is installed. Therefore this allocation is explicitly host-only CPython fallback; it does not claim container isolation or resource enforcement. If the exact pure model cannot run reproducibly on the host, STOP rather than approximate it.

## One-shot boundaries

Construction checks precede freeze. After freeze: candidate exactly once; independent auditor exactly once; zero retries. Any discrepancy is preserved as FAIL/HOLD. Only the separate construction test may run before the formal freeze. No task, GUI, model, input, network access by candidate, or user-facing randomization.

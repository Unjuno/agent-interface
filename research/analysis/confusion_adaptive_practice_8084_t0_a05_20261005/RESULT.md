# A05 result — `METHOD_PASS_SCOPED` / diagnostic screen `DOES_NOT_SUPPORT`

## H / T / D / C / U

**H.** Under finite repeated diagnostic trials, the A02 fixed-matrix eligibility rule (`span >= 0.25 AND peak >= 0.70`) may vary with sample size and may admit low-dispersion profiles.

**T.** Four authored stationary Bernoulli strata; `n={5,20,100}` per pair; 1,000 deterministic replicates per stratum/sample-size cell (12,000 rows). Candidate sees only opaque IDs, denominator, and observed success counts. Auditor alone sees latent rates.

**D.** Candidate and independent auditor each ran once in separate network-disabled, read-only WSLc containers; both exited 0. The auditor independently reconstructed all 12,000 generated count rows and candidate decisions with zero base errors. Five predeclared mutations were all rejected, including duplicate row IDs and altered denominators. `METHOD_PASS_SCOPED`.

The separate frozen diagnostic screen was **not supported**: low-dispersion true-ineligible profiles falsely activated the unchanged gate 376/1,000 (0.376) at n=20, exceeding the ≤0.05 limit. At n=100 the rate was 47/1,000 (0.047), just below that limit. Uniform-control false activations were 11/1,000 (0.011) at n=20 and 0/1,000 at n=100. Strong-stratum eligibility was 997/1,000 and 1,000/1,000 at n=20/100; margin-stratum eligibility was 852/1,000 and 987/1,000. Top-pair accuracy among activated true-eligible rows was 1.000/1.000 for strong and 0.984/1.000 for margin at n=20/100. Under the preregistered conjunctive rule, the A02 thresholds are not reliable at `n>=20` in this finite synthetic screen.

**C.** The result is sensitive to authored rates, stationary independent Bernoulli draws, fixed thresholds, and chosen diagnostic sizes. The low-dispersion stratum deliberately lies below both A02 activation criteria in latent truth. Finite Monte Carlo frequencies are exact for this deterministic seed set only; no confidence bound or population rate is inferred.

**U.** This does not estimate participant-specific confusion reliability, learning, task transfer, GUI risk, or a real diagnostic sample-size requirement. It does not invalidate A02's schedule construction result or justify T1/human allocation. Any more conservative estimator requires a separately frozen successor experiment and held-out synthetic rate families.

## Lineage and retained prior outcomes

- A01 `STOP_PREFORMAL_INPUT_ISOLATION` and A02 `METHOD_PASS_SCOPED` remain unchanged.
- A03 `STOP_AUDIT_INPUT_HANDOFF_PATH_ERROR`: candidate output existed, but its one auditor launch could not find the misplaced raw input; no audit accepted.
- A04 `HOLD_METHOD_GATE`: base rows were reconstructed, but a duplicate-row auditor mutation survived. Provisional A04 frequencies are not promoted.
- A05 is a fresh seed family and 1,000-replicate allocation; it does not reuse earlier candidate output. Its auditor verifies raw cardinality before mapping IDs.

WSLc warns that cgroup/swap limit capabilities are unavailable; 1 CPU/512 MiB were requested, not proven as hard limits. No Docker Desktop, GUI, model, participant, or live runtime was used.

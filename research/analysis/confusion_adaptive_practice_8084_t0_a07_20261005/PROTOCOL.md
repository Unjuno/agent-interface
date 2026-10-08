# Issue #8084 T0 A07 — fresh-seed fixed-gate frontier successor

## H / T / D / C / U (freeze before execution)

**H.** A stricter fixed span/peak gate may reduce false activations from weak, low-dispersion synthetic profiles while retaining activation on clear-positive profiles. If no frozen grid member meets both criteria at both sample sizes, these authored strata do not support one common fixed gate.

**T.** Independently simulate 5,000 diagnostic count triples per profile at `n ∈ {20,100}` for five null (`p00`–`p04`) and three clear-positive (`p05`–`p07`) profiles. Candidate sees opaque IDs, `n`, and counts only. Evaluate all 20 gates: span `{.25,.30,.35,.40,.45}`, peak `{.70,.75,.80,.85}` under `max(rate)-min(rate) >= span AND max(rate) >= peak`. Fresh A07 seed base is `8507000`, disjoint from A06's `8406000`: profile/n/replicate seed is `8507000 + profile_index*100000 + n*1000 + replicate`; pair seed is `key*10 + pair_index`; use CPython 3.12.10 `random.Random(seed).binomialvariate(n,p)`. Auditor independently reconstructs observations and decisions from `SCORING.json`.

**D.** Method pass only if all observations and candidate rows reconstruct exactly, base errors are zero, and five frozen mutations are rejected. Screen `EXISTS_GATE_IN_FROZEN_GRID_SCOPED` only if one grid member has a 95% Wilson lower bound ≥.80 for every positive profile and a 95% Wilson upper bound ≤.05 for every null profile, at both n values; otherwise `NO_GATE_IN_FROZEN_GRID_MEETS_BOTH_CRITERIA_SCOPED`. No post-result expansion or retry.

**C.** Authored stationary independent Bernoulli pairs, selected profile families, Python PRNG, finite seed set, and Wilson approximation. Taxonomy and grid are not empirically calibrated; profiles are not population samples.

**U.** Synthetic method/sensitivity evidence only; no participant confusion, real diagnostic sample size, learning/adaptation, T1, GUI/runtime/safety claims, and no revision of A02/A05/A06.

## Execution and isolation boundary

- Parent #8084 remains open. A07 is a distinct fresh-seed successor to A06; A06's launcher STOP is preserved unchanged and its allocation is not retried.
- Base main `f2b380c88` (full SHA in FREEZE.json); unique branch `research/8084-diagnostic-threshold-sensitivity-a07-20261005` and package directory.
- Windows x64; CPython `C:\Users\junny\AppData\Local\Programs\Python\Python312\python.exe` version 3.12.10, verified before freeze. Invoke this exact executable directly, not `py`/PATH lookup.
- Standard library only, no network by source design; no WSLc, Docker, GPU, GUI, model, participant, external data, or shared service. Candidate and auditor are separate serial processes with disjoint working directories. This host-process boundary is weaker than container isolation and makes no sandbox claim.
- Exactly one generator, candidate, auditor invocation. Freeze before fixture/candidate/auditor calls. No retry after freeze; retain first outcome.

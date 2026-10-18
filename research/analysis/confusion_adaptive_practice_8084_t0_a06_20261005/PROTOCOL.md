# Issue #8084 T0 A06 — finite operating frontier for fixed confusion gates

## H / T / D / C / U (freeze before execution)

**H.** A stricter fixed span/peak gate may reduce false activations from weak, low-dispersion synthetic profiles while retaining useful activation on clearly heterogeneous profiles. If no member of the frozen grid satisfies both operating criteria at both `n=20` and `n=100`, these authored strata do not support one common fixed gate.

**T.** Independently simulate 5,000 diagnostic count triples per profile at each `n ∈ {20,100}`. Use five held-out null profiles (`p00`–`p04`) whose peak is below .70 or whose pairwise dispersion is negligible, and three clear-positive profiles (`p05`–`p07`) with a uniquely highest pair and latent span ≥.35 / peak ≥.86. Candidate sees only opaque profile IDs, `n`, and three observed integer counts; it does not receive rates, null/positive labels, or profile class. Evaluate all 20 gates formed by span `{.25,.30,.35,.40,.45}` and peak `{.70,.75,.80,.85}` using the unchanged rule `max(rate)-min(rate) >= span AND max(rate) >= peak`. Generate each count with Python 3.12.10 `random.Random(seed).binomialvariate(n,p)`, where `seed = 8406000 + profile_index*100000 + n*1000 + replicate`, and pair-level seed is `seed*10 + pair_index`. Auditor independently reconstructs the full observations and candidate decisions from its hidden scoring file.

**D.** Method pass iff every observation and candidate row is independently reconstructed, base errors are zero, and five frozen mutations are rejected (flip one decision bit, duplicate a candidate row, alter an observation count, alter a gate threshold, remove a candidate row). The fixed-gate screen is `EXISTS_GATE_IN_FROZEN_GRID_SCOPED` iff one grid member has a 95% Wilson lower bound ≥.80 for activation on every positive profile and a 95% Wilson upper bound ≤.05 on every null profile, at both sample sizes; otherwise `NO_GATE_IN_FROZEN_GRID_MEETS_BOTH_CRITERIA_SCOPED`. No post-result grid expansion or allocation retry.

**C.** Authored stationary independent Bernoulli pairs, chosen held-out profile families, Python PRNG, finite 5,000-replicate seed sets, and a 95% Wilson approximation. The profile taxonomy and threshold grid are not empirically calibrated; family members are not a population sample.

**U.** Synthetic method/sensitivity evidence only. It does not estimate participant-specific confusion, establish a real diagnostic sample size, validate learning/adaptive practice, justify T1, or make GUI/runtime/safety claims. It does not revise A02/A05.

## Execution boundary and lineage

- Parent issue #8084 remains open; A06 is a distinct fresh T0 allocation after merged A03 STOP / A04 HOLD / A05 `METHOD_PASS_SCOPED` with a negative finite reliability screen.
- Base `main`: `19a6b723e58ccfd2b8265e88659589ef9223fcc9`; branch `research/8084-diagnostic-threshold-sensitivity-a06-20261005`; output path is this unique directory.
- Host: Windows x64, CPython 3.12.10. Standard library only; no network, WSLc, Docker, GPU, GUI, model, participant, external data or shared service. Candidate and auditor are separate serial Python processes with disjoint working directories; only frozen observed counts and candidate stdout are handed to the auditor.
- Exactly one fixture-generation, candidate, and auditor invocation. No retries after freeze. This host process boundary is weaker than a container; source has no network or subprocess use, and the record makes no sandbox-isolation claim.

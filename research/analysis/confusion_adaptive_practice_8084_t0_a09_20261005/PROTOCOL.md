# Issue #8084 T0 A09 — overdispersion robustness successor

## H / T / D / C / U

**H.** The two span/peak rules that passed A08 under fixed pair probabilities may or may not retain the frozen false-activation and sensitivity bounds when pair-specific rates fluctuate between diagnostic opportunities. If neither any frozen grid member meets both criteria, this authored overdispersion level does not support a common gate.

**T.** Simulate 5,000 triples per each of the same five authored null and three clear-positive mean profiles at n∈{20,100}; evaluate all 20 A08 gates unchanged. For each profile pair and replicate, draw a latent pair rate from `Beta(mean*40,(1-mean)*40)`, then draw a binomial count at n. Use CPython 3.12.10 `Random(seed).betavariate` and `binomialvariate`; seed base 8709000, with row key `8709000 + profile_index*100000 + n*1000 + replicate`, pair seed `key*10+pair_index`. This seed base is disjoint from A06/A07/A08 (8406000/8507000/8608000). Candidate sees only opaque IDs, n, and counts; it does not see truth or concentration. Independent auditor reconstructs every latent-rate draw and count from SCORING.json.

**D.** Method PASS only if observations and candidate output reconstruct exactly with zero base errors and all five frozen mutations are rejected. A grid member qualifies only if every positive profile has Wilson 95% lower activation bound ≥.80 and every null profile has upper bound ≤.05, at both n values. Report `EXISTS_GATE_IN_FROZEN_GRID_SCOPED` or `NO_GATE_IN_FROZEN_GRID_MEETS_BOTH_CRITERIA_SCOPED`. No threshold tuning or retry.

**C.** Beta concentration 40 is an authored stress level, not fitted to participants. Pair rates fluctuate independently per replicate; profile means, concentration, grid, PRNG, sample sizes and Wilson bounds are synthetic assumptions, not population estimates.

**U.** Synthetic robustness evidence only; no actual learner confusion, GUI distribution, diagnostic sample-size, learning, adaptive-practice benefit, T1, runtime, or safety claim. Does not change A08 or earlier allocations.

## Execution procedure

- #8084 remains open. A09 is a distinct model stress test with fresh seed/path; A06/A07/A08 observations are not reused.
- Base main is recorded in FREEZE.json; branch `research/8084-diagnostic-overdispersion-a09-20261005`; package path `research/analysis/confusion_adaptive_practice_8084_t0_a09_20261005/`.
- Windows x64; exact CPython 3.12.10 interpreter `C:\Users\junny\AppData\Local\Programs\Python\Python312\python.exe`.
- Before generator: add package using `git add --sparse`, require zero exit; commit freeze, require zero exit; verify freeze blob in HEAD and clean package. Any precondition failure aborts all formal calls.
- After successful freeze, invoke generator, candidate, auditor once each via that executable and record each status. No retries.
- Host-only standard-library processes; no WSLc or Docker (management gate untouched), network, GPU, GUI, model, participant, external data, or shared service. No container-isolation or resource-enforcement claim.

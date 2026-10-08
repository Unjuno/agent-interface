# Issue #8084 T0 A08 — fresh-seed fixed-gate frontier successor

## H / T / D / C / U

**H.** A stricter fixed span/peak gate may reduce false activations from weak, low-dispersion synthetic profiles while retaining activation on clear-positive profiles. If no member of the frozen grid meets both criteria at n=20 and n=100, the authored strata do not support one common fixed gate.

**T.** Simulate 5,000 count triples/profile at n∈{20,100} for five null profiles (p00–p04) and three clear-positive profiles (p05–p07). Candidate receives opaque IDs, n, and counts only. Evaluate the 20 gates from span {.25,.30,.35,.40,.45} × peak {.70,.75,.80,.85} under max(rate)-min(rate)≥span AND max(rate)≥peak. A08 fresh seed base 8608000 is disjoint from A06 8406000 and A07 8507000. Row seed = 8608000 + profile_index×100000 + n×1000 + replicate; pair seed = row seed×10 + pair_index. Use CPython 3.12.10 random.Random(seed).binomialvariate(n,p). Auditor independently reconstructs rows/decisions from SCORING.json.

**D.** Method PASS only if observations and every candidate row independently reconstruct, base errors are zero, and five frozen mutations are rejected. A grid member qualifies only if Wilson 95% lower activation bound ≥.80 on every positive profile and upper bound ≤.05 on every null profile, at both n values. Otherwise report `NO_GATE_IN_FROZEN_GRID_MEETS_BOTH_CRITERIA_SCOPED`. No grid expansion or allocation retry.

**C.** Authored stationary Bernoulli pairs and selected profile classes; PRNG finite seed sets; Wilson interval approximation; thresholds and strata are not empirically calibrated or sampled from a population.

**U.** Synthetic method/sensitivity evidence only. No participant confusion, real diagnostic sample size, learning/adaptive benefit, T1, GUI/runtime/safety claim; does not revise A02/A05/A06/A07.

## Frozen execution procedure

- Parent #8084 stays open; A08 is distinct from prior STOPs, with new path and disjoint seed; no previous raw observation is reused.
- Base main full SHA recorded in FREEZE.json. Branch `research/8084-diagnostic-threshold-sensitivity-a08-20261005`; unique path `research/analysis/confusion_adaptive_practice_8084_t0_a08_20261005/`.
- Windows x64; exact interpreter `C:\Users\junny\AppData\Local\Programs\Python\Python312\python.exe`, CPython 3.12.10, verified before formal run.
- Before any generator call: `git add --sparse` only the A08 package; require exit 0; commit freeze; require exit 0; verify HEAD contains FREEZE.json and package worktree has no uncommitted files. Any failure is fatal and means generator/candidate/auditor all remain uncalled.
- Then call the exact interpreter once for generator, once for candidate (from candidate/), and once for auditor (from auditor/), checking and recording each exit before proceeding. No retries; preserve the first STOP/FAIL.
- Standard library only; no network by source design. No WSLc or Docker (their management gate remains closed and is not touched), GPU, GUI, model, participant, external data, or shared service. Separate host processes are weaker than containers; no isolation guarantee is claimed.

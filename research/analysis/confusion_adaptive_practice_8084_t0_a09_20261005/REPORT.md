# Issue #8084 T0 A09 — overdispersion robustness screen

## Result

Disposition: `METHOD_PASS_SCOPED`; diagnostic screen: `NO_GATE_IN_FROZEN_GRID_MEETS_BOTH_CRITERIA_SCOPED`.

The 80,000-row fixture used independent Beta(μ·40,(1−μ)·40) pair-rate draws per replicate, then binomial observations at n=20 or 100. The independent auditor reconstructed all rows and decisions with zero base errors; all five frozen mutation controls were rejected. None of the 20 frozen gates met both the ≥.80 positive Wilson lower-bound and ≤.05 null Wilson upper-bound criteria across every profile/sample size.

Examples expose the sensitivity/specificity conflict at n=20:

| gate (span, peak) | worst positive Wilson lower | worst null Wilson upper | limiting cases |
|---|---:|---:|---|
| (0.45, 0.85) | 0.62 | 0.04 | positive sensitivity p07; null p01 |
| (0.45, 0.80) | 0.72 | 0.06 | positive p07; null p00 |
| (0.45, 0.70) | 0.78 | 0.07 | positive p07; null p00 |
| (0.40, 0.80), A08-qualified | 0.79 | 0.10 | positive p07; null p01 |
| (0.40, 0.75) | 0.84 | 0.12 | positive p07; null p00 |

The A08-qualified gates (0.40,0.80) and (0.45,0.70) both lose the joint criterion under this authored overdispersion stress: tightening specificity lowers positive activation; relaxing gates raises false activations. The raw auditor JSON has exact counts and intervals for every gate/profile/n value.

## H / T / D / C / U

- **H:** In this chosen overdispersion model, the A08 operating frontier does not robustly retain a single gate satisfying both bounds; no gate in the unchanged grid qualifies.
- **T:** Same eight authored profile means and 20 fixed gates as A08; fresh seed base 8709000, 5,000 replicates/profile/n, Beta concentration 40. Earlier A06/A07/A08 observations were not reused.
- **D:** `METHOD_PASS_SCOPED`, 80,000 independent reconstructions, zero base errors, all five mutations rejected; diagnostic decision `NO_GATE_IN_FROZEN_GRID_MEETS_BOTH_CRITERIA_SCOPED`.
- **C:** Concentration 40 is an authored stress setting, not estimated from learners; pair-rate draws are independent between pairs and replicates. Profile taxonomy, PRNG, sample sizes, threshold grid, and Wilson bounds remain synthetic assumptions.
- **U:** No actual learner or GUI data, calibrated operating point, participant-specific diagnosis, real sample-size recommendation, learning/adaptive benefit, T1, runtime, or safety conclusion.

## Execution evidence

- Freeze commit `6f8f3d476c2e229686e5cde22f2249697a761ce6`, base main `cc2eb4a205bb8f8001b1baed05f482208c0b0935`; frozen source hashes in `FREEZE.json`.
- CPython 3.12.10 exact path in the freeze. Generator exit 0 (~3.75 s), candidate exit 0 (~1.33 s), auditor exit 0 (~37.64 s); each formal process invoked once. Full stdout/stderr and handoff files are retained.
- Construction tests 5/5 normal and 5/5 under `-O` before freeze. Two earlier static-assertion wording mismatches were corrected pre-freeze and retained in `results/construction-initial-failure.txt`; no formal calls occurred until tests passed and freeze commit was verified.
- Host-only process separation; no WSLc, Docker, network, GPU, GUI, model, participant, or external data. This is not a container/isolation or resource-enforcement claim.

# Issue #8084 T0 A08 — frozen-grid synthetic screen

## Result

Disposition: `METHOD_PASS_SCOPED`; diagnostic screen: `EXISTS_GATE_IN_FROZEN_GRID_SCOPED`.

The fresh A08 synthetic fixture contained 80,000 rows (8 authored profiles × 2 sample sizes × 5,000 replicates). The independent auditor reconstructed all observations and candidate decisions with zero base errors; all five frozen mutation controls were rejected. Exactly two frozen grid members met both Wilson-bound criteria for every profile at both sample sizes:

| span | peak | worst positive Wilson lower bound | worst null Wilson upper bound |
|---:|---:|---:|---:|
| 0.40 | 0.80 | 0.8269 (p07, n=20) | 0.0428 (p00, n=20) |
| 0.45 | 0.70 | 0.8038 (p07, n=20) | 0.0293 (p00, n=20) |

At n=100, all five null profiles had 0/5,000 activations (Wilson upper bound 0.0008 each) for both qualifying gates. The other positives' lower bounds also exceeded 0.80. Full per-gate/per-profile counts and 95% Wilson intervals are in `results/auditor.stdout.json`.

## H / T / D / C / U

- **H:** The frozen synthetic hypothesis receives scoped support: at least two gates in this authored grid distinguish the selected low-dispersion/null from clear-positive profiles with the preregistered finite criteria. This does not establish that those profiles model learners or GUI variants.
- **T:** Five authored null profiles, three authored positives, n=20/100, 5,000 fresh A08 replicates per profile/sample size, and the frozen 20-gate grid. Fresh seed base 8608000 is disjoint from A06 (8406000) and A07 (8507000); A07's unfrozen fixture was not reused.
- **D:** Auditor returned `METHOD_PASS_SCOPED`, zero errors, and rejected flipped-bit, duplicate-row, altered-count, altered-threshold, and removed-row mutations. Two grid gates met every stated Wilson criterion.
- **C:** Authored stationary independent Bernoulli pairs, finite seed set, selected profile taxonomy, PRNG and Wilson approximation. This is not a representative population, and the grid is not calibrated on observed data.
- **U:** Synthetic method/sensitivity only. No human learning, participant-specific diagnosis, real sample-size recommendation, adaptive-practice benefit, T1, GUI/runtime, or safety claim. No change to prior A02/A05/A06/A07 dispositions.

## Execution evidence

- Freeze commit `b670f06816ee5d9690d06acb7eec39a86317e11a`, based on main `24cbb631b972eee1723d2372adf53032dfdaab20`; frozen source hashes are in `FREEZE.json`.
- CPython 3.12.10 at the exact absolute path in `FREEZE.json`; standard library only. Generator exit 0 (~3.08 s), candidate exit 0 (~0.59 s), auditor exit 0 (~22.87 s); each formal process was invoked once. Stdout/stderr and all handoff inputs are retained.
- Two auditor allowlist preflight checks initially refused to launch because the local check compared filename ordering/case too strictly; no auditor process started on either preflight. The corrected exact-set check passed before the single auditor invocation. No candidate/generator rerun followed these preflights.
- A post-formal construction-suite invocation produced 3 pass / 1 fail because its initial-empty-candidate-directory assertion was run after the frozen generator had correctly placed `observed_counts.json` there. The pre-freeze construction suite passed 4/4 normal and under `-O`; the postrun failure is preserved in `results/postrun-construction-test-failure.txt`. No source change or allocation retry followed.
- Construction suite: 4/4 normal and 4/4 under `-O` before freeze. `git diff --check` passed.
- Host-only Windows process boundary; no container, WSLc, Docker, network, GPU, GUI, model, participant, or external data. No resource-enforcement or isolation claim.

The numerical screen is a finite simulation result under the frozen authored assumptions—not a validated operational threshold. A separate preregistered and governed human study would be needed for learner or GUI claims.

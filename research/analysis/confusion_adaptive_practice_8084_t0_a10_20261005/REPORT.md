# Issue #8084 T0 A10 — finite overdispersion frontier

## Result

Disposition: `METHOD_PASS_SCOPED`; across the five-arm finite screen, `EXISTS_GATE_IN_FROZEN_GRID_SCOPED` only in the fixed-rate reference arm (κ=null), where one gate qualified: span 0.40 / peak 0.80. No gate qualified in any finite-concentration Beta-binomial arm (κ=20, 40, 80, 160).

The 160,000-row independent audit reconstructed every observation and candidate decision with zero base errors; all five mutations were rejected. For the same gate (0.40, 0.80), the most difficult positive and null profiles at either n had these bounds:

| arm | worst positive Wilson lower | worst null Wilson upper | joint gate criteria |
|---|---:|---:|---|
| κ=20 | 0.7536 (p07, n=20) | 0.1569 (p00, n=20) | fail |
| κ=40 | 0.7767 (p07, n=20) | 0.1065 (p00, n=20) | fail |
| κ=80 | 0.7876 (p07, n=20) | 0.0675 (p01, n=20) | fail |
| κ=160 | 0.8036 (p07, n=20) | 0.0588 (p00, n=20) | fail |
| fixed rates (κ=null) | 0.8191 (p07, n=20) | 0.0495 (p00, n=20) | pass |

The sensitivity bound reaches its ≥0.80 threshold by κ=160 in this finite sample, but the null upper bound remains above 0.05 until the fixed-rate reference. This is a discrete authored frontier, not an estimated continuous cutoff. The reference arm used 2,000 replicates, versus 5,000 in A08; therefore the fixed-rate qualifying gate count (one here vs two in A08) should not be read as a contradiction or a stable population difference. Full exact gate/profile/n/arm counts and Wilson intervals are in `results/auditor.stdout.json`.

## H / T / D / C / U

- **H:** In this selected model, qualification varies across concentration: no finite κ in {20,40,80,160} supports a frozen gate under both bounds; the fixed-rate reference qualifies one gate.
- **T:** Five hidden arms, eight authored profiles, n=20/100, 2,000 replicates per profile/sample-size/arm, 20 unchanged gates; 160,000 rows. Fresh A10 seed base 88100000 is disjoint from A06–A09. No prior observations reused.
- **D:** `METHOD_PASS_SCOPED`, zero reconstruction errors, all five mutations rejected. `EXISTS_GATE_IN_FROZEN_GRID_SCOPED` is limited to arm a04 (fixed rates), gate span .40 / peak .80; finite concentration arms all return no qualifying gate.
- **C:** Only four selected finite concentrations plus one fixed-rate reference; authored means/profile classes; independent latent beta draws; finite seeds/sample sizes; Wilson intervals. κ is not estimated or calibrated from participants.
- **U:** No real diagnostic operating threshold, learner confusion, GUI/practice distribution, sample-size guidance, T1, human-learning benefit, runtime or safety conclusion.

## Execution evidence

- Freeze commit `d7dfa634f064c86580e00d08ff188ae5cececba6`, base main `f75ad203f41126c2382175aed398639796fe6d0d`; frozen source hashes in `FREEZE.json`.
- CPython 3.12.10 exact path in freeze. Generator exit 0 (~8.06 s), candidate exit 0 (~1.64 s), auditor exit 0 (~66.63 s), each invoked once. Full stdout/stderr and handoff files retained.
- Construction suite passed 5/5 normally and 5/5 under `-O` before freeze. Frozen source hashes verified after the run; `SHA256SUMS` covers the complete package.
- Host-only standard-library processes; no WSLc, Docker, network, GPU, GUI, model, participant or external data. No container/isolation/resource-enforcement claim.

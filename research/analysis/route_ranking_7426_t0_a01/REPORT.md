# Issue #7426 T0 result — A01

**Disposition: `PASS_METHOD_SCOPED` on the preregistered synthetic method check.** Independent exact-rational enumeration agrees with the candidate for six fixtures and five mutations. This does not rank real routes, estimate user preferences, establish safety in a live system, or change the #57 integrated-evaluation outcome.

The enumerator evaluates all 28 rational simplex points at denominator 6 for each full-domain axis (784 task-mix/value-weight pairs). Controlled reversal cases hold one axis fixed, producing 28 pairs each. The separate audit transcribes fixture values independently and recomputes the pair scores and exact winner counts using its own direct arithmetic loop.

| Fixture | Declared result | Grid result | Equal-mix/equal-weight comparator |
|---|---|---|---|
| Componentwise dominance | Robust A | A wins 784/784 | A (`4/3` vs `7/3`) |
| Crossed faster/costlier tradeoff | No universal winner | A 288, B 288, tie 208 / 784 | Tie (`25/9` each) |
| Task-mix reversal, latency-only | Mix-dependent | A 12, B 12, tie 4 / 28 | Tie (`25/9` each) |
| Value-weight reversal, stratum 1 | Value-dependent | A 12, B 12, tie 4 / 28 | Tie (`8/3` each) |
| Missing outcome in a possible stratum | Hold | 441 of 784 pairs incomplete; no partial winner region is reported | Hold |
| Lower-cost route fails safe-release gate | Exclude before ranking | A excluded; only B eligible, so no comparison | Hold |

The fixed aggregate conceals both planted reversals by returning a tie, while the set-valued method exposes equal-sized A/B regions on the declared rational grid. These grid proportions are counts of enumerated parameter points, **not probabilities or preference frequencies**. The robust-dominance result is conditional on the full simplex grid and the synthetic table.

All five mutations behaved in the specified direction: breaking one dominance cell removed robust-A status; changing one latency cell changed the exact task-mix winner counts; narrowing the admissible value set produced robust A for the latency-only value; passing the hard gate admitted A and yielded robust A; and filling the missing outcome removed the HOLD. Full details and canonical-LF hashes are in `independent-audit.json` and `SHA256SUMS`. Run `python verify_hashes.py` to normalize Windows CRLF checkouts to canonical LF before checking the manifest.

## Limits / next use

The finite rational grid does not enumerate the continuous simplex, sampling uncertainty, nonlinear utility, cross-outcome interactions, or uncovered task strata. It is a method sanity check only. T1 remains conditional on a qualified matched #57 comparison, per-stratum retained outcomes, and a preference/workload set frozen before examining route contrasts. No empirical recommendation follows.

## Reproduction

From this directory, run `python rank.py`, `python audit.py`, then `python verify_hashes.py`. `rank.py` writes candidate output; `audit.py` independently checks the fixtures and mutation cases against it. Python standard library only. No external process, model, GUI, provider, or network call is made by either script.

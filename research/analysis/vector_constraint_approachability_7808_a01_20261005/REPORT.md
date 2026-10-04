# Issue #7808 — vector-constraint approachability A01

**Disposition: `PASS_METHOD_SCOPED`; the declared finite-sequence hypothesis is supported only on the frozen synthetic workload.** No real route cohort or runtime behavior was tested.

## Frozen question

Allocation `VCA-7808-WSLC-A01-20261005` used current main `aa2e4b623b2f4ccdcbc8e294535bab09c0092f30`. The target is the convex upper-bound box for two soft costs: model-boundary count and elapsed-cost units. Three hard-eligible routes are available per opportunity. The vector-debt controller uses positive cumulative debt and context forecasts, with forecast useful-effect as the tie-break. Baselines are fixed equal-weight scalar cost and independent per-axis threshold/freeze with minimum total predicted cost. An independent exhaustive oracle enumerates every admissible finite route sequence.

## Result

The candidate ran once and exited 0. The independent raw-only auditor ran once and exited 0 with `PASS_METHOD_SCOPED` and no errors. There were no retries or post-freeze source changes.

| Frozen case | Vector policy result | Independent finding |
|---|---|---|
| Feasible alternating contexts; target `[1.1, 1.1]` | 12/12 verified useful effects; mean `[1.1, 1.1]` | Fixed scalar and threshold/freeze each produce 0 effects at `[0.2, 0.2]`. The exhaustive oracle finds 505,249 feasible route sequences out of 531,441 and a 12-effect feasible sequence. |
| Infeasible target `[0.1, 0.1]` | Mean `[0.3625, 0.3625]`; claim `OUTSIDE_TARGET` | Oracle finds no feasible route sequence; the controller does not claim convergence. |
| Delayed and missing feedback | 10 verified effects; row 7 remains unresolved; claim `UNKNOWN_INCOMPLETE_FEEDBACK` | Delayed feedback is delivered with its row identity. The missing row is not imputed as zero. |
| One extreme realized episode | Mean `[1.467, 0.95]`; claim `OUTSIDE_TARGET` | Maximum observed episode cost remains `[10, 2]`, so the average does not conceal the extreme. |

The five construction tests passed under both host Python and the pinned WSLc image. They include the clean independent replay plus four mutation controls: zero-imputed missing feedback, hard-gate bypass, false convergence on the infeasible target, and attempted/no-effect relabeling. All four mutations were rejected.

## H / T / D / C / U

- **H:** Supported on this exact authored alternating-context sequence. The vector selector met both soft targets and produced more independently scored useful effects than both frozen online baselines, with no hard-gate failures.
- **T:** Four cases and three policies were executed in one isolated CPU container; the separate integer-ID auditor replayed all decisions, feedback, means, maxima, gates, claims, and exhaustive oracle counts.
- **D:** `PASS_METHOD_SCOPED`. Candidate and auditor each ran once. The audit error list is empty; all mutation controls reject.
- **C:** The result depends on the predeclared context tradeoff and forecast utility tie-break. A different cohort, cost scale, target, or comparator could remove the advantage; fixed weights may be preferable when the user specifies them.
- **U:** The fixture is deterministic and authored. Outcomes, forecasts, opportunity order, and the effect oracle are known by construction; there is no real task heterogeneity, causal route benefit, latency, safety, deadline, human-preference, or product evidence.

## Construction history and resources

An early host construction process was stopped after uncached repeated oracle enumeration became too slow. After caching the oracle, an initial host run was 4/5 because one assertion expected six baseline effects; inspection showed zero under the written minimum-cost comparator. That assertion was corrected before freeze. Final host and WSLc construction runs each passed 5/5. No formal raw output existed during construction.

WSLc emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The run requested one CPU and 128 MiB, used a cached pinned image, disabled networking, and did not pull. Configured memory is not treated as independently verified enforcement.

## Delivery snapshot

Main advanced six commits (36 paths) after the experiment freeze. The current `docs/CURRENT_GOAL.md` blob and `research/analysis/README.md` blob are unchanged from the frozen base; the six commits do not touch the package path. Issue #7808 remains open with no new comments or matching branch. The evidence branch is based on current main `dccf55e264f434ca27f2948fe53be09919047819`; the experiment's source base remains the frozen `aa2e4b623b2f4ccdcbc8e294535bab09c0092f30`.

## Next evidence step

Run a read-only eligibility check for repeated retained route opportunities with comparable task strata, independent per-opportunity effect scoring, and complete source-bound soft-cost vectors. If none exist, retain this as method-only evidence and do not allocate a live experiment from this result.



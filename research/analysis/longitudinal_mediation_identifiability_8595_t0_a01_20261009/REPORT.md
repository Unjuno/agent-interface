# Issue #8595 T0 A01 — result

## Disposition

`PASS_METHOD_SCOPED`. The deterministic finite candidate completed once and the independent auditor completed once, with no retries. The auditor exactly reconstructed 1,536 rows across four structural cases and passed 1,576 checks; all six mutation controls were rejected. The raw candidate SHA-256 is `56c4b57c2f18215d6789ebe06d6e84246d360aee58b0f3459a1398aa17dee534`.

## Results

| Case | Route total assignment effect | Longitudinal interventional contrast | Naive baseline-only contrast | Status |
|---|---:|---:|---:|---|
| No mediation, exposure-induced state | 0.125 | 0 | 0.00357143 | Estimated |
| Known mediation | 0.16666667 | 0.04166667 | 0.04523810 | Estimated |
| Mediation with exposure-induced state confounding | 0.16666667 | 0.04166667 | 0.04523810 | Estimated |
| Positivity failure | 0.33333333 | — | 0.08333333 | `NOT_IDENTIFIABLE_POSITIVITY` |

The no-mediation longitudinal estimator returned zero, while the naive contrast was positive and exceeded the frozen `0.001` diagnostic floor. In the two identified mediated cases, the estimator matched the structural oracle at `1/24`. The failed-positivity case returned no point estimate even though the naive comparator emitted one. The hidden-confounding pair retained identical observed `(A,M,Y)` cell counts and route total effects, while the model-intervention truths differ (`0.8` versus `0`); disposition was `NOT_IDENTIFIABLE_OBSERVATIONAL_EQUIVALENCE`. The randomized mediator intervention returned `0.8`. A separate component factorial interaction was zero, distinct from the `1/24` mediator-distribution contrast.

## Scope and limits

This supports the declared finite-model bookkeeping and identification rules under the authored equations. Exhaustive equal-weight enumeration replaced the Issue's seeded simulation, so there is no Monte Carlo error in these fixture results. It does not establish sequential exchangeability, mediator identification, or a causal mechanism in any real application, product, user, model, or GUI. No container semantics were tested; this was stdlib-only host CPU work without network, model, GUI, user data, or external effects. Authority remains `NONE`.

## Custody and verification

The preregistration is [Issue #8595 comment](https://github.com/Unjuno/agent-interface/issues/8595#issuecomment-6069166001). The frozen input commit is `feca206f23b983cc2cc28b322a6dd4bb65cfa284`; candidate and auditor each ran once under CPython 3.12.13. Exact command output, stderr, exit, timestamps, raw result, audit summary, and hashes are retained in `results/`. See [FREEZE.json](FREEZE.json), [PLAN.md](PLAN.md), [spec.json](spec.json), and [SHA256SUMS.json](SHA256SUMS.json).

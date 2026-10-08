# Issue #5424 T2 — typed action-class burn-rate simulation

## Disposition

`PASS_TYPED_PRIMARY_BURN_GATE_SCOPED_WITH_COMPLETION_TRADEOFF`.

The preregistered primary-exposure, incident-attribution, recovery-bound, row-replay, summary-replay, and corruption-control gates passed after a documented summary-only audit correction. The broader hypothesis is only partially supported: task completion fell modestly under the typed controller in every fault regime, and the common-cause regime increased severe alternate-route exposure. This is not evidence of net production benefit.

## Frozen comparison and execution

The experiment compared `NO_FREEZE`, a per-route two-consecutive-severe breaker, and a typed controller with 12/48-step route windows plus a distinct incident-parent budget. The same preregistered input corpus was replayed for all policies: four regimes × 24 fixed seeds × 192 steps, producing 18,432 input rows and 55,296 policy rows. See [PLAN.md](PLAN.md), [EXECUTION.md](EXECUTION.md), and [SOURCE_MANIFEST.md](SOURCE_MANIFEST.md) for H/T/D/C/U, source hashes, image, commands, and execution limits.

## Results

Each number below is the total over 4,608 policy-steps per regime. `After signal` counts executed primary severe/catastrophic events after the first severe signal on the affected route(s); for common cause it counts across both routes. `Severe primary / alternate` counts all executed severe/catastrophic events. `Completed` is the simulator's primary-success or successful-alternate count, not an application task score. `Recover max` is the largest number of steps after the fixed repair boundary until all affected routes are unfrozen.

| Fault regime | Policy | After signal | Severe primary / alternate | Completed | False-freeze opportunities | Recover max | Max non-completion streak |
|---|---|---:|---:|---:|---:|---:|---:|
| Route drift | No freeze | 302 | 347 / 8 | 4,574 | 0 | 0 | 1 |
| Route drift | Local breaker | 216 | 261 / 10 | 4,565 | 162 | 9 | 1 |
| Route drift | Typed budget | **130** | **175 / 10** | 4,557 | 351 | **5** | 1 |
| Rare catastrophe + burst | No freeze | 136 | 178 / 5 | 4,576 | 0 | 0 | 1 |
| Rare catastrophe + burst | Local breaker | 100 | 141 / 6 | 4,570 | 77 | 10 | 1 |
| Rare catastrophe + burst | Typed budget | **58** | **99 / 8** | 4,566 | 208 | **7** | 2 |
| Shared parent incident | No freeze | 413 | 446 / 90 | 4,489 | 0 | 0 | 3 |
| Shared parent incident | Local breaker | 219 | 252 / 119 | 4,453 | 206 | 11 | 5 |
| Shared parent incident | Typed budget | **89** | **122 / 137** | 4,428 | 280 | **5** | 5 |

Typed budget reduced the preregistered post-signal primary severe count in every fault regime versus both comparators. Total executed severe primary+alternate counts were 185 vs 271/355 (drift), 107 vs 147/183 (catastrophe), and 259 vs 371/536 (common cause), ordered typed/local/no-freeze. All 24 affected traces per fault regime returned affected routes within 12 steps; typed maxima were 5, 7, and 5 respectively.

Important counterevidence: in the shared-incident regime the alternate route was itself correlated with the outage. Typed fallback severe exposure rose to 137 (vs 119 local, 90 no-freeze) while completion fell to 4,428 (vs 4,453, 4,489). The policy shifts exposure toward the fallback even though combined severe count drops in this particular fixture. The controller cannot make an unsafe fallback safe. False-freeze opportunities were substantial (351 route-drift, 208 catastrophe, 280 common-cause); thresholds and probe fidelity are policy assumptions.

Stationary input produced the same 40 primary and 4 alternate severe outcomes and 4,597 completions under every policy; typed had five false-freeze steps but no completion change. This fixed corpus does not yield a false-alarm rate estimate.

## Audit

Audit v1's first result remains an explicit `FAIL_RAW_AUDIT`; it matched all event rows and rejected 4/4 mutations but miscomputed the no-fault stationary signal denominator. The frozen raw-only audit-v2 correction independently replayed all rows, reproduced the full summary, reported zero errors, and again rejected 4/4 mutations. See [AUDIT_REPAIR.md](AUDIT_REPAIR.md) and both retained audit JSON files. No experiment/raw rerun was used to obtain audit-v2.

## Scope and next boundary

This deterministic simulator supports a bounded mechanism claim about cumulative typed burn versus a consecutive breaker under the exact hand-authored traces and weights. Fixed seeds are reproducibility, not population sampling. It does not establish calibrated action-class SLOs, trustworthy incident attribution, production GUI statistics, human impact, live fallback safety, runtime behavior, safety certification, or product efficacy. Before any runtime integration, separately test fallback common-cause dependence, event-label corruption/missingness, window/threshold sensitivity under preregistered grids, recovery probes under false-clean rates, and safe-alternative admission/abstention. Do not treat this result as a release policy.

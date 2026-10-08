# #1695 Evidence-dependent compute RUN/WAIT break-even

Decision: **PASS_EVIDENCE_COMPUTE_RUN_WAIT_BREAK_EVEN_SCOPED**

After the #1687 hard feasibility gate, one current feasible job is compared over a declared horizon with:
- invalidation probability `p`;
- conditional stable-world waiting loss `g` if the scheduler WAITs instead of RUNning now;
- conditional invalidation-world obsolete-compute loss `w` if the scheduler RUNs instead of WAITing.

Common downstream/rebuild work is cancelled. The incremental expected costs are:
- RUN: `p*w`;
- WAIT: `(1-p)*g`.

Therefore the exact cost difference is `p*w - (1-p)*g`. When `g+w>0`, the break-even invalidation probability is `p* = g/(g+w)`:
- RUN if `p < p*`;
- WAIT if `p > p*`;
- TIE at equality.

If `g=w=0`, both policies tie for every `p` and no threshold is fabricated.

## Exact verification

The formal Fraction grid contains 4,913 `(p,g,w)` rows:
- RUN: 2,410;
- WAIT: 2,410;
- TIE: 93;
- threshold/direct expected-cost mismatches: 0;
- zero-zero rows: 17/17 ties;
- nonzero threshold rows: 4,896.

The naive comparator `p*w` versus `g`, which omits the stable probability factor `(1-p)`, disagrees on 1,210 rows. The richer expression is therefore decision-relevant, not algebraic decoration.

The expected-value layer was also composed with the #1687 stale/deadline gate across 1,458 states. Hard-gate override violations were 0; all 162 inclusive exact-deadline rows remained feasible where current.

## Scope

The theorem does not estimate `p`, `g`, or `w`. They must be calibrated in a commensurate utility/cost unit for a specific job class. Correlated/time-varying invalidation, preemption, partial reuse, multiple jobs and resource contention remain outside this one-horizon model. REUSE semantics remain separate under #1675.

Independent audit and four corruption controls pass; formal invocation 1, reruns/replacements/tuning 0.

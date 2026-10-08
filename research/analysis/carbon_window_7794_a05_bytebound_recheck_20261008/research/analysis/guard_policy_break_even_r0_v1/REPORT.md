# Guard-policy break-even analytical R0 — retained result

Issue #1646. ROADMAP owners: guard-cost risk tradeoff and automatic pre-guard vs postcondition-only selection.

## Disposition

**PASS_GUARD_POLICY_BREAK_EVEN_ANALYTIC_SCOPED**

One source-frozen formal invocation; reruns0/replacements0/tuning0.

## Result

The one-step recoverable-route cost model has an exact selector.

Let:

| Symbol | Meaning | Dimension |
|---|---|---|
| p | probability state is stale at admission | dimensionless probability |
| c_g | pre-guard acquisition + validation cost | one chosen cost unit |
| s | P(guard rejects given stale) | dimensionless probability |
| f | P(guard rejects given fresh) | dimensionless probability |
| c_y^s | yield/replan cost after true stale rejection | same cost unit as c_g |
| c_y^f | false-reject yield/replan cost | same cost unit |
| c_f | stale-action failure + recovery cost | same cost unit |

Postcondition-only incremental expected cost:

`C_post = p c_f`.

Pre-guard incremental expected cost:

`C_guard = c_g + p[s c_y^s + (1-s)c_f] + (1-p) f c_y^f`.

Therefore

`Delta = C_guard - C_post = N - p D`

with

`N = c_g + f c_y^f`

and

`D = s(c_f - c_y^s) + f c_y^f`.

For recoverable routes:

- if `D > 0`: choose GUARD exactly when `p > N/D`, POST when `p < N/D`, tie at equality;
- if `D = 0`: POST unless `N = 0`, in which case the policies tie;
- if `D < 0`: guard cannot be cheaper; only the degenerate `N=0,p=0` point ties.

Perfect guard `s=1,f=0` reduces to:

`p* = c_g / (c_f - c_y^s)`.

### Dimension check

Every term in `C_post`, `C_guard`, `N`, and `pD` has the same chosen cost dimension. Probabilities are dimensionless. The threshold `N/D` is dimensionless, as required for comparison with `p`.

This means wall time, token money, task-loss utility, and irreversible harm cannot be silently mixed. A route must first define one commensurate utility/cost model.

## Formal verification

Exact `fractions.Fraction` arithmetic:

- directed edge cases;
- exhaustive grid: **4,860** tuples;
- deterministic random: **250,000** tuples;
- total recoverable comparisons including directed cases: **254,868**;
- hard-safety controls: **10,002**.

Results:

- closed-form vs direct expected-cost mismatch: **0**
- hard-safety postcondition-only selections: **0**
- exact tie cases: **676**
- D<=0 cases: **71,580**
- threshold >1 cases: **109,780**
- exact threshold tie classifications: **188**
- naive `c_g < p c_f` mismatches versus direct optimum: **142,927**

Thus the sensitivity, false-reject, and yield-cost terms are not algebraic decoration; omitting them changes the selected policy on a large part of the frozen corpus.

The independent auditor imports no candidate/formal implementation. It regenerates the exact Fraction corpus, parameter-stream digest and decision-stream digest:

- parameter stream: `1d7b7fabf9449bad9bfaa5c9e7ffcd740d47684fc60819e4626b8383eb537128`
- decision stream: `c55a2fd1287a2d62b1bfde99e5c73f5c0ac8e8be40cec834877a15789e81d1c2`

Primary audit and six corruption controls pass.

## Safety override

This selector is **not** a safety relaxation.

If a stale action effect is forbidden by the correctness/safety contract, the route is outside the recoverable-cost optimization domain. A pre-effect correctness gate remains mandatory unless stale impossibility is independently proven. No finite expected failure cost can authorize a forbidden wrong effect.

## Existing measurements as examples, not thresholds

Using the retained p95 guard acquisition costs only as algebraic examples, and assuming a perfect guard, zero yield cost, and wall-time as the sole cost unit:

- #1179 AF_UNIX p95 0.039589 ms gives p*=0.39589% for a hypothetical 10 ms failure cost, 0.039589% for100 ms, 0.0039589% for1000 ms.
- #1172 private-X11 ROI p95 0.221238 ms gives p*=2.21238%, 0.221238%, 0.0221238% for those same hypothetical failure costs.

These are **not** measured route stale probabilities, failure costs, or production thresholds.

## Scope

The derivation is one admission decision with stationary parameters. It does not estimate p, sensitivity, false-reject rates, recovery utility, repeated-action correlation, model tokens, or task speed.

## Next legal rung

Calibrate the frozen selector from retained route evidence without changing the formula:

1. choose one route with measured guard cost;
2. estimate stale incidence and recovery/yield cost from independently retained outcomes;
3. report an interval for p and cost rather than a single optimistic point estimate;
4. classify the policy only when the interval lies wholly on one side of the break-even surface; otherwise retain UNKNOWN/MEASURE_MORE.

Hard-safety routes remain outside the cost selector.

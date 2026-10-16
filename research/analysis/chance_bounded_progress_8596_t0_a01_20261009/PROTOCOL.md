# Frozen protocol — UNJUNO-8596-CHANCE-BOUNDED-PROGRESS-T0-A01-20261009

## H / T / D / C / U

**H.** On authored finite event models, an exact deadline-reachability interval can distinguish (1) a nontrivial model-conditioned chance of progress from absence of an all-traces finite progress bound, (2) an optimistic midpoint probability from the robust lower bound, and (3) two delay laws with the same mean but different deadline tails. A separate all-reachable-transitions safety check must reject any policy with a reachable unsafe transition regardless of its progress probability. Missing probability justification must produce `NOT_IDENTIFIABLE` without fabricated bounds.

**T.** Pure-Python standard-library finite calculation. For geometric response, enumerate interval endpoints for every opportunity and all progress/miss histories through horizons 1–4. Compare the universal sure-bound verdict with exact lower/upper finite-horizon reachability and an explicitly naive midpoint estimate. At the frozen deadline of four opportunities, compare interval fixtures `[1/4,1/2]` and `[1/2,3/4]` against an illustrative threshold `τ=4/5`. Compare deterministic two-opportunity completion with a `9/10` one-opportunity, `1/10` eleven-opportunity tail law; both have exact mean two, but the deadline is four. Include a rare trigger with probability `1/32` whose consequence is selected adversarially as safe-yield or unsafe, and an unmodeled case. Candidate uses exact rational dynamic programming; the raw-only auditor independently enumerates endpoint assignments and every finite event history. No marker truth is exposed as a policy observation.

**D.** `PASS_METHOD_SCOPED` requires exact agreement between candidate outputs and independent enumeration for every frozen horizon/fixture; geometric histories with positive miss probability must not be reported as a universal finite guarantee; the midpoint must not substitute for the interval lower bound; equal-mean tail cases must retain different exact deadline probabilities; every reachable unsafe transition must fail `HARD_SAFETY` regardless of probability; the unknown case must be `NOT_IDENTIFIABLE` with no numeric probability; and all seven frozen output mutations must be rejected. `H_SUPPORTED_SCOPED` additionally requires the high-probability geometric case to have lower bound at least `τ` while still lacking an all-traces finite bound, and the wide interval’s midpoint to pass `τ` while its robust lower bound does not. Any mismatch is `FAIL_METHOD`; absent/invalid inputs or source custody is `HOLD_UNCERTAIN`. The threshold is only an authored sensitivity discriminator; no real task-admission claim is tested.

**C.** An all-traces finite guarantee or explicit safe-yield may be the only appropriate control contract when transition intervals cannot be justified. The chosen threshold and finite model could make the chance contract look useful without corresponding to any user task. A correct calculation cannot correct a wrong transition model.

**U.** Exact model-conditioned probabilities only. The fixture does not identify real delay distributions, disturbances, application markers, stationarity, GUI observability, wall-clock latency, safe actions, or task completion. An authored hard-safety pass does not prove physical or application safety. No transfer to runtime admission follows.

## Variables and units

| Symbol | Meaning | Unit/type | Frozen domain |
|---|---|---|---|
| `N` | Deadline horizon | opportunity count (dimensionless integer) | 1–4; primary N=4 |
| `p_t` | Progress probability on opportunity `t` before the marker | dimensionless exact rational | endpoints of the case interval |
| `L_N`, `U_N` | Lower and upper probability of marker by N | dimensionless exact rational | [0,1] |
| `τ` | Illustrative synthetic decision threshold | dimensionless exact rational | 4/5; fixture demonstration only |
| `q` | Rare disturbance-trigger probability | dimensionless exact rational | 1/32 at opportunity zero |
| `T` | First marker opportunity | opportunity count (dimensionless integer) | fixture-defined discrete support |

No physical seconds are modeled. An opportunity is one discrete event transition and is not a measured wall-clock interval.

## Frozen fixture cases

1. `geometric_wide`: independent chance interval `[1/4,1/2]` on each opportunity until progress absorbs; N=4; `τ=4/5`.
2. `geometric_high`: interval `[1/2,3/4]` on each opportunity; same N and threshold.
3. `rare_disturbance_safe_yield`: trigger q=1/32 at opportunity zero, followed on no-trigger by `geometric_wide`; on trigger, safe yield and no progress. All reachable states remain safe.
4. `rare_disturbance_unsafe`: the same trigger, but the environment may choose an unsafe consequence. The edge is adversarial and reachable; probability mass is not used to waive the hard-safety check.
5. `same_mean_delay`: compare support `{(T=2,1)}` with `{(T=1,9/10),(T=11,1/10)}`. Both means are two opportunities; report exact `P(T≤4)` and `P(T>4)`.
6. `unmodeled_delay`: no justified transition distribution or interval. Return `NOT_IDENTIFIABLE`, with numeric probability fields absent.

Geometric bounds are computed over a rectangular set: on each pre-marker opportunity, the selected probability may be either interval endpoint. The all-traces verdict is separate: because the miss branch remains reachable at each opportunity, no finite N is a sure bound even where the probability of reaching the marker tends to one over an unbounded horizon.

## Execution and source identity

- Intake base: current `main` `0621713407d42c5a3922572b2fe57222f175e9a2`.
- Allocation: `UNJUNO-8596-CHANCE-BOUNDED-PROGRESS-T0-A01-20261009`.
- Branch: `research/8596-chance-bounded-progress-t0-a01-20261009`.
- Candidate: `python3 -B runner.py --output results/first-outcome` exactly once.
- Auditor: `python3 -B auditor.py --output results/first-outcome --result results/first-outcome/audit.json` exactly once after the candidate; no formal retry or tuning.
- Runtime: one local CPython process per role, standard library only, CPU-only; no container setup/pull and no shared GUI, VM, model, GPU or external runtime used.
- Candidate owns its rational recurrence. Auditor imports neither candidate nor runner and independently enumerates every endpoint vector and binary progress history, checks raw outputs and mutations.

## References

Hahn, Hartmanns & Hermanns, “Reachability and Reward Checking for Stochastic Timed Automata,” ECEASST 70 (2014), [publisher record and DOI](https://doi.org/10.14279/tuj.eceasst.70.968). This work studies model-conditioned lower/upper reachability bounds for stochastic timed automata; it does not validate the fixture's probabilities.

PRISM, [uncertain models documentation](https://www.prismmodelchecker.org/manual/PropertySpecification/UncertainModels), documents robust min/max verification over interval probabilities. The experiment uses a separate small exact-rational implementation and makes no PRISM-equivalence claim.

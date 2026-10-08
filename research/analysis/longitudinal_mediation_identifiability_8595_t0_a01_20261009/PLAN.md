# Issue #8595 T0 A01 — longitudinal mediation identifiability

## Scope and status

One-shot deterministic finite method experiment for [Issue #8595](https://github.com/Unjuno/agent-interface/issues/8595), based on current `main` `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`. It tests declared estimands and identification gates in authored structural models. It grants no runtime, product, or action authority and makes no claim about real human, GUI, or model behavior.

## H / T / D / C / U

**H.** Exact longitudinal standardization over the post-assignment state `L` recovers the declared interventional mediator-distribution contrast in the finite cases where sequential exchangeability, consistency, and positivity hold; it returns `NOT_IDENTIFIABLE_POSITIVITY` when the required source stratum is absent. A baseline-only comparator can report a spurious pathway when exposure changes `L` and `L` confounds mediator and outcome. Identical observed `(A,M,Y)` laws with different true mediator effects must be labeled observationally nonidentified.

**T.** Enumerate every equally weighted exogenous assignment in four frozen binary SCM cases (384 rows each): no mediator effect with exposure-induced `L`; known mediation with `L` independent of route; mediation with exposure-induced `L`; and structural positivity failure. Estimate the stochastic interventional contrast `psi(g1)-psi(g0)` under outcome assignment `A=1` and its induced `L` distribution, standardizing equally over baseline `D`; this is not a natural indirect effect. Compare with a naive version omitting `L`. Add an exact hidden-confounding observational-equivalence pair, a randomized mediator intervention positive control, and a separate 2x2 component interaction to demonstrate that it is a different estimand. The finite support is fully enumerated rather than Monte Carlo seeded, removing sampling error while preserving the Issue's causal contrasts and identification cases. Candidate and auditor are separate stdlib programs; auditor reconstructs all rows and estimands using exact `Fraction` counts and rejects six mutations.

**D.** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs all 1,536 rows and reported quantities; the identified longitudinal estimates equal their structural oracle; the no-mediation longitudinal effect is zero while the naive contrast exceeds `0.001`; positivity failure yields no point estimate; the hidden pair has identical observed counts, route total effect `0.4` in both worlds and mediator effects `0.8` versus `0`; randomized mediator control equals `0.8`; component interaction remains `0` while the mediator contrast is `1/24`; and all six mutation controls are rejected. Any failed equality, support check, or false identification is `FAIL_METHOD`; an auditor/source/output contract failure is retained as `HOLD_AUDIT` or `STOP` and is never retried. Each formal command runs once; retries are zero.

**C.** Exact enumeration may make this selected finite fixture unusually easy; a baseline-only comparator may differ in other populations; assumed equations are not empirically validated; a randomized mediator intervention is an idealized positive control.

**U.** This establishes only finite-model bookkeeping and identification behavior under the authored equations. It does not establish sequential exchangeability in an application, real-world mediation, causal product effects, model quality, user outcomes, GUI behavior, or live action. It uses host CPU and no container because no container semantics or isolation claim is tested; there is no network, model, GUI, user data, or external effect.

## Construction before freeze

Six construction tests pass under CPython 3.12.13. A separate construction-only candidate/auditor replay reconstructed 1,536 rows with 1,576 checks and rejected 6/6 mutations. No formal allocation has been invoked and formal output files are absent. One construction fixture expectation was corrected from an erroneous decimal to the independently derived exact contrast `81/638`; an additional regression test now covers a positive-mass target stratum with absent mediator-source support. Candidate and auditor were also changed before freeze to enumerate both binary `L` levels and ignore only zero-mass target levels.

## Frozen commands

Candidate (once): `python3.12 research/analysis/longitudinal_mediation_identifiability_8595_t0_a01_20261009/candidate.py --spec research/analysis/longitudinal_mediation_identifiability_8595_t0_a01_20261009/spec.json --output research/analysis/longitudinal_mediation_identifiability_8595_t0_a01_20261009/results/candidate.raw.json`

Auditor (once, only after candidate exits zero and raw hash is recorded): `python3.12 research/analysis/longitudinal_mediation_identifiability_8595_t0_a01_20261009/auditor.py --spec research/analysis/longitudinal_mediation_identifiability_8595_t0_a01_20261009/spec.json --raw research/analysis/longitudinal_mediation_identifiability_8595_t0_a01_20261009/results/candidate.raw.json --output research/analysis/longitudinal_mediation_identifiability_8595_t0_a01_20261009/results/audit.raw.json`

The formal commands are authorized only after this freeze is committed and pushed and its exact commit and hashes are preregistered on Issue #8595. Candidate/auditor invocation budget: one each; retries: zero.

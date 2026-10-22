# Issue #7993 — repeated-cohort IPCW A02 construction gate

Status: **CONSTRUCTION_ONLY / HOST**. This is not a frozen allocation or formal result. It repairs the structural omissions identified in exploratory A01: candidate/oracle data separation, raw-only reconstruction, digest-bound oracle truth, and executable UNKNOWN / mutation controls.

Base selected at branch creation: current main `5db548aa351c8ccd351831485d5e5940a4967ff3`. Additive namespace intended for repository publication: `research/analysis/verifier_maturity_censoring_7993_superpopulation_a02_construction_20261005/`.

## H / T / D / C / U

**H.** With known, positive label-follow-up probabilities `pi(X)` and conditional independence of follow-up from binary verifier error `Y` given `X`, the Horvitz–Thompson mean `(1/N) Σ RᵢYᵢ/pi(Xᵢ)` targets the realized finite cohort in expectation over follow-up and the declared superpopulation risk in expectation over independently generated cohorts. Complete-case averaging can be biased when both outcome risk and follow-up propensity vary by X. If assumptions/positivity are not declared, output should be UNKNOWN; if declared, the estimate remains explicitly assumption-conditional.

**T (construction, executed).** One 32×40 fixture, seed 7993002. Candidate input includes assignments, X, known pi, observed flag, and label only when observed; oracle input is a separate object holding full outcomes. One candidate invocation and separate raw-only audit function. Mutation controls cover dropped assignments, changed hidden truth against the pre-mutation oracle digest, propensity mismatch, altered candidate output, invalid/missing propensity support, hidden-label leakage, and missing independence contract. These are host construction checks, not the Issue's formal repeated-cohort allocation.

**T (formal proposal, not executed).** After a fresh freeze and usable eligible container/resource boundary: generate 20,000 independent N=400 cohorts with two equal strata, `P(Y=1|X=0)=0.40`, `P(Y=1|X=1)=0.10`, and known follow-up probabilities `(0.25,0.75)`. The exact population target is `1/4`. Candidate sees only its public file; raw-only auditor gets a distinct oracle file and frozen oracle SHA-256. Preserve per-cohort estimates and all source/input/output hashes. A separate zero-support and missing-assumption control must return UNKNOWN. A candidate estimate is always tagged ASSUMPTION_CONDITIONAL, never an unconditional guarantee.

**D.** Construction gate passes only when the candidate cannot receive oracle data, raw auditor reconstructs every assigned row/checkpoint from independent truth, every mutation is rejected, and unsupported conditions emit UNKNOWN. For the proposed repeated-cohort method slice, require `abs(mean(HT)-1/4) <= 4*s_HT/sqrt(20,000)`, where `s_HT` is the sample standard deviation across cohort-level HT estimates; also report empirical dispersion. This is a Monte Carlo implementation check, not a confidence guarantee for real data. Complete-case is a diagnostic baseline with analytic limit `7/40`, not a guarantee. A separate zero-support and missing-assumption control must return UNKNOWN. Any superpopulation point-estimate result remains distinct from finite-cohort all-assigned bounds in A01. The broader Issue remains open regardless.

**C.** All-assigned finite-cohort bounds may already be sufficient; known propensities are unrealistic in some workloads; HT may be high variance; an assumption-conditioned point estimate may add no decision value. If so, report NO_INCREMENTAL_VALUE rather than promote IPCW.

**U.** A finite authored design does not validate real verifier labels, estimated censoring models, informative censoring, time-varying delays, missing-not-at-random follow-up, shift, or production calibration. No coverage/risk guarantee, runtime safety, or action authority is tested.

## Construction evidence

Commands on macOS host Python 3.14.5 (standard library only):

```sh
python3 -m unittest -v
python3 -O -m unittest -v
python3 -c 'from generate_fixture import generate; import candidate,auditor; p,o=generate(); out=candidate.evaluate(p); print(out["status"], auditor.audit(p,o,out,auditor.oracle_digest(o)))'
```

Observed: **11/11 tests pass** in ordinary mode and **11/11** under `-O`; fixture candidate status `ASSUMPTION_CONDITIONAL`; raw-only audit `ok=true`, `errors=[]`, 1,280 assigned rows and 32 cohorts reconstructed. No container, full-scale repeated-cohort run, independent external review, or formal allocation occurred. The shared OrbStack image-store error from the preceding stop remains unresolved; no runtime repair/pull/prune/restart was attempted. Treat this construction result only as readiness evidence.

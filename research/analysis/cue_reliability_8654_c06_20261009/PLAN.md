# Issue #8654 C06 — stochastic-outcome support enumeration (pre-run freeze)

Base main: 2a0016575c105a04ccd972920329c291b86d7d0b.
Branch: research/8654-c06-stochastic-support-20261009.
Namespace: research/analysis/cue_reliability_8654_c06_20261009/.
This is a new allocation over stochastic outcomes; it does not rerun C05's propensity-misspecification allocation.

## H/T/D/C/U
- **H:** In a finite two-context/two-action partial-feedback setting with Bernoulli rewards and positive logged diagnostic propensities, the exact design expectation of HT/IPW equals the all-action oracle. Individual finite histories can still be noisy; any history missing a context-action cell is labelled UNIDENTIFIABLE. A greedy policy has zero alternative-action support and must abstain.
- **T:** Exhaustively enumerate all joint action-choice and reward-outcome histories for STABLE, REVERSAL, and GLOBAL_SHIFT regimes over four trials per context. Diagnostic sampling selects the cue-opposed action with probability 1/4 (otherwise 3/4); reward probabilities are 0.8/0.2, 0.2/0.8, and 0.55/0.15 respectively. Enumerate 65,536 diagnostic histories and 256 greedy histories per regime. Retain compact raw ledgers with exact integer probability numerators before audit. Independently reconstruct every row, six unit-mass groups, support labels, HT design expectation, and corruption controls.
- **D:** PASS_METHOD_SCOPED only if all 197,376 histories are unique and reconstruct; each of six probability masses is exactly 1; exact known-propensity HT expectation equals the oracle in all diagnostic regimes; every greedy history is UNIDENTIFIABLE; and 4/4 audit mutations are rejected. This does not test policy learning or assert that exploration is beneficial.
- **C:** The result is exact for this finite Bernoulli design; equal four-trial horizons and stationarity may make natural support/learning easier or harder in other designs.
- **U:** One-step synthetic method evidence only. No GUI, model, user, sequential carryover, runtime, safety, task benefit, or authorization claim.

Frozen candidate enumerates the finite design; frozen auditor is separately implemented and reads only saved raw files plus the frozen design constants. Raw files must be committed before invoking the auditor. One execution, no retries.

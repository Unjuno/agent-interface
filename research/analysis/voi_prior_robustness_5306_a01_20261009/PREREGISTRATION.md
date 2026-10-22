# VOI prior-set robustness — A01

Issue: #5306, unverified prior-set robustness addendum dated 2026-10-01. This is a new diagnostic slice after the merged one-step and complementary-check results; it does not rerun or revise those allocations.

## H / T / D / C / U

**H.** A point-prior VOI action can hide STOP/CONTINUE reversals across a declared prior set near its decision boundary. An exact prior-set label should expose that sensitivity while retaining robust STOP and CONTINUE controls and enforcing mandatory/freshness/deadline gates.

**T.** Run the exact-rational finite candidate once on `cases.json`, then run the separately implemented independent auditor once on the saved raw output. The six fixed cases cover a point decision at the reversal boundary, robust STOP, robust CONTINUE, a correlated duplicate with no incremental evidence, a continuation check infeasible by the deadline, and incomplete mandatory coverage. The three policies are point VOI, point VOI plus a fixed `1/5` utility-unit margin, and a prior-set robustness label. Construction tests also mutate away a reversing prior and attempt to override mandatory/deadline gates.

**D.** The **diagnostic construction gate** passes only if exact candidate output and independent reconstruction agree, the point case is `PRIOR_SENSITIVE` while robust controls remain decidable, duplicate evidence has zero gross value, and all three mutations are rejected. The **Issue-level evidence gate** is separate: `P` in this fixture is hand-authored to bracket a boundary; no empirical calibration or independent outcome cohort supports its plausibility. Therefore the broader #5306 robustness hypothesis remains `HOLD_PRIOR_SET_NOT_EMPIRICALLY_SUPPORTED` even if the diagnostic gate passes.

**C.** This is a deliberately finite expected-loss model with a perfect fresh discriminator or an already-seen duplicate. A source-bound typed receipt may carry the needed bit more cheaply than a model call; the fixture neither models that delivery cost nor establishes calibration. A fixed checklist or deterministic selective policy may remain simpler.

**U.** No empirical held-out outcome table, probability-coverage estimate, actual verifier, GUI, model, latency, token, cost, safety, or product result is measured. Results are exact only for these authored inputs; the selected prior intervals are not claimed to be evidence-supported.

## Frozen model and variables

For prior `p = P(state is persisted)`, an optional perfect new check avoids expected false-completion loss `L(1-p)`. Net VOI is `L(1-p)-c`. A check already represented by the current evidence has gross incremental value zero. Ties select STOP. `ROBUST_STOP` and `ROBUST_CONTINUE` require the same decision at every enumerated prior; mixed decisions yield `PRIOR_SENSITIVE`. A valued but deadline-infeasible continuation yields `YIELD_CHECK_INFEASIBLE`. Incomplete mandatory checks yield `YIELD_MANDATORY_INCOMPLETE` before any recommendation can be acted upon.

| Symbol | Meaning | Unit / type | Domain |
|---|---|---|---|
| `p` | Prior probability that the effect is persisted | dimensionless rational | `[0,1]` |
| `L` | Loss assigned to a false completion claim | dimensionless normalized utility units | positive rational |
| `c` | Cost assigned to one optional check | same normalized utility units | nonnegative rational |
| `m` | Fixed confidence-margin comparator | same normalized utility units | nonnegative rational |
| `L(1-p)-c` | Net value of a perfect fresh check | normalized utility units | rational |

Utility units are fixture weights, not seconds, dollars, tokens, or measured risk. No physical time or resource quantity is inferred.

## Exact expected discriminator

With `L=10`, `c=1`, the net-value sign changes at `p=9/10`. The prior-sensitive case contains `22/25`, `9/10`, and `47/50`, producing net values `1/5`, `0`, and `-2/5`; tie-to-STOP makes the point policy stop while the set contains a CONTINUE point. The robust controls use priors wholly below or above this boundary. The confidence margin is fixed at `1/5` before the run and is not tuned from candidate output.

Candidate and input source identities will be recorded in `FREEZE.json` before either formal invocation. The one-shot candidate and independent auditor write only under `results/`. No allocation is consumed by construction tests. This CPU-only exact enumeration uses only the Python standard library on the task's isolated worktree; it does not use or inspect shared Docker/OrbStack state.

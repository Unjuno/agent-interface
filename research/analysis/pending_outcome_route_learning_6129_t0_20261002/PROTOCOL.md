# Issue #6129 T0: pending-aware route evidence card

## H/T/D/C/U

- **H**: a pending-aware route card will avoid unsupported route ranking from receipt speed or complete cases; it will report no preference for equal evidence, select only when exact outcome bounds separate, and abstain under ambiguous attribution / unsupported censoring.
- **T**: one synthetic, finite, five-case fixture at update time 5. The candidate sees only `visible.json`; the auditor alone sees `truth.json`. The cases cover receipt/effect inversion with possible outcome-dependent censoring, equal null, known-window noninformative censoring with separated bounds, ambiguous attribution/informative censoring, and all-pending initial exposure.
- **D**: pass only if all 5 predeclared classifications and all identified exact bounds match, pending observations remain `[0,1]` rather than negative/success, nonidentified cases expose no actionable bounds, and two mutation controls are rejected. No data pruning or posthoc threshold selection.
- **C**: synthetic deterministic CPU-only T0; exact rational arithmetic; one candidate invocation and one independent audit invocation; pinned Python 3.12 slim image; candidate and auditor in separate network-disabled, read-only-root containers.
- **U**: no empirical route efficacy, live system, safety, GUI, model, human, bandit-regret, causal/product effect, or production-routing claim. No T1 authorization or field collection follows from this result.

## Freeze and execution

`FREEZE.json` hashes the visible fixture, truth fixture, candidate, auditor, protocol and tests before execution. Candidate container mounts only `visible.json`, `candidate.py` and a separate writable result directory. Audit container mounts visible data, truth, candidate output and auditor source, but not candidate source. Source and input mounts are read-only, network is disabled, root filesystem is read-only, capabilities are dropped, and resource limits are fixed in `RUN.json`.

The candidate is invoked once. The auditor is invoked once. Retries are zero. Exact finite fixture reconstruction is a method check, not a statistical estimate.

## Outcomes

Formal outcome is determined only from frozen `truth.json` and auditor output. Any missing/mutated input, unexpected case, bounds mismatch, misclassification, or failed mutation control is `FAIL`. A container/runtime failure before candidate execution is `STOP_INFRA`; an execution after start with invalid output is `FAIL`. Scope is restricted to this synthetic fixture.

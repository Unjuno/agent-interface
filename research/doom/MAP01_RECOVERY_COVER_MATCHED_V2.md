# MAP01 bounded recovery-cover matched preregistration v2

Status: **CONSTRUCTION FROZEN; NO LIVE LEASE GRANTED**

Task: `O3-PH48-G7-RECOVERY-MATCHED-V2-FREEZE-001`  
Base: `5486ea20b417a80903619a384744cf9ac38d5a52`  
Allocation ID reserved by this construction: `map01-recovery-cover-matched-live-v2-01`

## Why v2 exists

Draft PR #74 froze the right causal question—matched unauthored coast versus explicitly bounded recovery—but it predates three retained findings now required for a valid formal allocation:

1. the `map01-measurement-integration-live-02` workflow ran twice despite a one-run/no-retry contract, so that formal allocation is invalid even though the measurement mechanics replicated;
2. `audit_map01_terminal_score_agreement_v1.py` now fail-closes exact agreement between the final independent scorer sample and the established v12 terminal score;
3. `formal_allocation_launch_owner_v1.py` now provides deterministic canonical launch ownership for future one-shot allocations, with the explicit caveat that the workflow still needs non-cancelling serialization around the ownership check.

V2 incorporates those constraints before any implementation or live execution. It does not rewrite PR #74, the consumed live-02 workflow, or any retained result.

## Question

When the slow planner is pending under matched MAP01 conditions, does an explicitly admitted, source-bound, guarded and expiring local recovery program reduce measured no-retained-input time **and** produce independent useful outcome evidence relative to unauthored coast, without weakening stale-authority refusal or release correctness?

This is deliberately stricter than asking whether a key can stay down. A continuity-only improvement without independent useful-effect evidence is classified `HOLD_MECHANISM_ONLY`, not scientific `PASS`.

## Frozen comparison

### COAST_CONTROL

- planner-wait fallback: unauthored empty coast;
- input authority during that fallback: none.

### BOUNDED_RECOVERY

- planner-wait fallback: separately admitted bounded program;
- source observation binding required;
- observable guard required;
- explicit expiry required;
- stale source or guard failure cancels;
- terminal empty release must be verified;
- one recovery lease is capped at 1500 ms.

All other declared conditions are matched. The intended arm difference is only planner-wait fallback behavior.

## Experimental-validity gate before the formal step

A future workflow/runner must use a **new versioned path and separate lease**. Before either formal arm may execute it must retain evidence that:

- exactly one run owns `map01-recovery-cover-matched-live-v2-01`;
- the current run is `PASS_CANONICAL_OWNER` under the retained launch-owner algorithm;
- contenders are serialized with non-cancelling workflow semantics before ownership is accepted;
- any non-owner, missing-current, malformed or duplicate launch fails closed before model/GUI/OS-input work;
- the strict terminal-score agreement audit is part of the frozen post-run gate.

The consumed live-02 workflow is immutable and must not be edited to test this machinery.

## Measurement contract

Primary retained quantities are:

- planner-wait interval;
- direct retained-input lower/upper bounds;
- no-retained-input lower/upper bounds;
- first positive independent progress event;
- first negative independent progress event;
- terminal score difference between matched arms;
- verified release latency;
- stale-authority admissions;
- release failures.

Independent scorer state remains scorer-only. It must not be delivered into controller/planner-visible event streams.

## Decision rule

### PASS

All hard and exposure gates pass; bounded recovery strictly lowers the no-retained-input upper bound for at least one matched planner-wait interval; and independent outcome evidence is useful in the same direction—either an earlier positive independent event or a strictly better matched terminal score—without an earlier matched negative event.

### HOLD_MECHANISM_ONLY

Safety and exposure pass and recovery reduces no-retained-input time, but the matched allocation provides no independent useful-effect or terminal-score advantage. Retain the continuity result; do not market it as useful-control efficacy.

### FAIL

Any hard gate fails, including duplicate/non-owner formal launch, terminal-score disagreement, stale-authority admission, release failure, scorer leakage, missing terminal release, or an earlier matched harmful outcome without an earlier positive outcome.

### UNCERTAIN

Clock/interval evidence cannot establish direction, or the recovery path is not actually exposed before planner completion, or matched independent outcome evidence is uninterpretable.

### HOLD

The allocation is valid and safe but too sparse for promotion. Preserve the first result and redesign only under a new allocation/version.

## H / T / D / C / U

**H — falsifiable hypothesis.** Explicit bounded recovery can reduce measured no-retained-input time during planner latency and yield independently useful outcome evidence under at least one matched interval while preserving all frozen safety and launch-integrity gates.

**T — minimum test.** One separately authorized, first-outcome matched allocation containing both frozen arms under the same declared fixture/seed/model/prompt/schema/runtime/instrumentation constraints. At least one recovery interval must acknowledge retained input before planner completion. No same-allocation retry.

**D — disposition.** Use exactly `PASS`, `HOLD_MECHANISM_ONLY`, `FAIL`, `UNCERTAIN`, or `HOLD` from the preregistration. No post-hoc threshold relaxation.

**C — competing explanations.** Recovery can merely add movement without useful effect; can accelerate harm; can appear better because clocks or release bounds are misaligned; can exploit privileged scorer state; or can look valid only because a duplicate formal run was selected after the fact.

**U — uncertainty.** Sparse independent useful events, one fixed MAP01 regime, model stochasticity, clock mapping, interval censoring, and workflow/API visibility races remain. One positive matched allocation would justify only the scoped claim frozen in the preregistration.

## Product Hunt claim boundary

If and only if scientific `PASS` is retained, the strongest allowed scoped claim is:

> In this matched MAP01 allocation, explicitly bounded local recovery reduced planner-wait idle control and produced independent useful outcome evidence while preserving stale-input refusal and verified release.

If the result is `HOLD_MECHANISM_ONLY`, the page may say only that measured no-input planner-wait was reduced while safety gates held; it must state that useful task benefit was not established.

Human-level reaction, general DOOM competence, general GUI reliability, general speedup, and model-quality improvement remain forbidden extrapolations.

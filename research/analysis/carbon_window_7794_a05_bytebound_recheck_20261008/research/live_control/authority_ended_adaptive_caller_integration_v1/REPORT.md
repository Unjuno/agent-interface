# `authority_ended` → exact adaptive caller v3 integration v1

Status: **PASS_CALLER_INTEGRATION** for a frozen model-free transcript block. This is a caller-semantics result, not live efficacy or production promotion.

## Question

The retained dual-lifetime executor can end physical input authority at a scheduled owner deadline, verify empty release, and obtain one passive post-release observation under a separate lifecycle. That event is `authority_ended`, not task success.

The exact current `adaptive_acquisition_caller_v3.py` has no `authority_ended` execution status. Raw `authority_ended` therefore fails closed as an unknown execution decision, but cannot be used as a typed replan boundary. This experiment changes one thing only: a narrow bridge translates a fully evidenced `authority_ended` receipt into the caller's existing `safe_yield(reason=authority_unavailable)` vocabulary.

The exact caller source is unchanged. Git blob: `7faf042304728ce91a3e4f89d465b251ea0bf70d`.

## Candidate contract

The bridge accepts `authority_ended` only when controller-visible evidence proves:

- verified release and empty key/button state;
- zero post-release input admissions;
- nonnegative completed-step count;
- exactly one passive post-authority capture;
- a new sequence (`sequence_advanced=true`);
- no observation error;
- observation completed inside its lifecycle deadline;
- post-authority evidence grants no input authority;
- old input-program tail resumed zero steps.

It deliberately ignores `score_agreement`: the independent scorer is not caller-visible authority.

A valid receipt maps to:

`safe_yield / authority_unavailable / completed_actions=N`

Under unchanged caller v3, this returns `EXECUTION_INCOMPLETE`; the caller does not invoke `verify_effect` and therefore cannot emit `TASK_SUCCEEDED` from the authority-end event.

## Frozen transcript block

Source rows: the three retained real-MAP01 `quiet_hold` rows from `research/doom/container_dual_lifetime_discovery_v1/quiet_hold_result.json`, Git blob `0627dba669903d3d8cc6e707cae9b9d329a623e5`.

Per source row:

- one valid transcript;
- one privacy control with only `score_agreement=false` (must classify exactly like valid because scorer is invisible);
- nine one-fault controller-visible mutations: missing post observation, stale/non-advanced sequence, unverified release, post-release input admission, old-tail revival, input-authority regrant, late observation, nonempty keys, observation error.

Total: **33 transcripts**.

## First frozen outcome

Decision: **PASS_CALLER_INTEGRATION**.

- valid receipts: **3/3** → `EXECUTION_INCOMPLETE / authority_unavailable`;
- scorer-privacy controls: **3/3** → identical classification;
- injected controller-visible faults: **27/27** → `CALLER_FAILED` fail-closed;
- fault transcripts reaching `TASK_SUCCEEDED`: **0/27**;
- total `verify_effect` calls across all 33 transcripts: **0**;
- hard failures: **0**.

Formal result SHA-256: `ad4fd31c4447085d9c49bf86ae72477c0826b25459f7eecdbc4646b3c1c613c4`.

## Interpretation

This closes one semantic integration gap: `authority_ended` can become a typed *replan boundary* without becoming semantic completion. The post-release observation is a prerequisite for bridge acceptance; missing/stale post-release evidence stops the caller.

It also preserves scorer isolation: changing an independent scorer field alone has no effect on caller classification.

The current mapping is intentionally conservative. Invalid receipts become generic `CALLER_FAILED` rather than a richer typed `WAIT_POST_AUTHORITY_OBSERVATION`. A future shared-caller version may introduce such a typed wait state, but this experiment does not modify the caller API to obtain a favorable result.

## H / T / D / C / U

**H.** A narrow evidence gate can integrate `authority_ended` into an existing caller without allowing task-success inference or privileged scorer leakage.

**T.** Exact caller v3, three retained real-MAP01 quiet-hold receipts, 27 one-fault controller-visible mutations, three scorer privacy controls, one frozen CPU-only transcript execution; zero model/GUI/OS-input calls.

**D.** PASS at transcript-integration scope: valid receipts map to execution-incomplete replan boundary, every visible fault fails closed, no effect verification or task success is reached.

**C.** Generic caller failure is safe but operationally coarse; a richer typed wait/retry state may reduce unnecessary model escalation. Fault injection does not replace a live caller session.

**U.** No frontier model, no live next-action admission, no concurrency race, no observation delivery loss after the terminal object has been assembled. The next gate should exercise the same bridge in a two-dispatch session: after `authority_ended`, a second semantic dispatch must be impossible without the valid post-release observation, and allowed only after that observation while still requiring ordinary fresh revalidation/input admission.

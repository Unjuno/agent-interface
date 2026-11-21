# Current-main Win32 finite recovery horizon positive control

Date: 2026-11-21  
Frozen HEAD: `069aa17599f6f640403fda29f09f521f8c8efd7d` (after PR #10370)  
Host: Windows, CPython 3.11.9  
Scope: current-main public stdio recovery protocol tests with synthetic backend/supervisor. No native GUI or input was used; no runtime behavior changed.

## Results

Three existing tests were run once each in normal and optimized Python:

1. **Mid-program authority expiry:** 1/1 PASS (4.077 s normal; 3.948 s `-O`). One program emission presses SHIFT, then the lease expires during the wait. Later CTRL is not emitted. The recovery receipt releases CTRL and SHIFT and records both neutral; cancellation is `recovered`/release confirmed. The action/task remains UNKNOWN/null, replay is denied. Exact events and receipts are under `artifacts-{normal,optimized}/source-receipts/`. This test does not establish a separate late-input horizon.
2. **Exact public stdio orphan recovery:** 1/1 PASS (7.844 s normal; 7.847 s `-O`). The source attempt stays UNKNOWN. A distinct recovery generation produces a receipt with `release_confirmed=true`, a 2,000,000,000 ns neutral horizon, 22 observations spanning 2.109 s (normal) / 2.110 s (`-O`), and maximum observed gap 110 ms. The exact recovery call remains queryable; no application operation is invoked, task success stays null, and replay stays denied. Receipt/request/close raw files are retained under `orphan-recovery-{normal,optimized}/`.
3. **Invalid horizon negative control:** 1/1 PASS (9.876 s normal; 9.865 s `-O`). The fake recovery receipt claims a 2-second horizon and `late_input_horizon_verified=true` but supplies only one observation; the public caller keeps recovery UNKNOWN and release unconfirmed, and dispatch returns `invalid_request/ORPHAN_RECOVERY_UNRESOLVED`. Raw is retained under `invalid-horizon-{normal,optimized}/`.

For the two stdio orphan-recovery tests, `run_retained_case.py` and `run_retained_invalid_case.py` only redirect the test's temporary directory to an invocation-specific evidence path. The unittest body and runtime source are unchanged. The exact command variants, source hashes, conditions and receipt metrics are in `conditions.json`.

## Delayed old-input adversarial horizon test

The actual `OperationCancellationSupervisor` test `test_delayed_down_during_recovery_horizon_keeps_owner_fenced` passes 1/1 normally (0.805 s) and under `-O` (0.832 s). It uses separately spawned producer, recovery helper, and observer helper processes. A controlled old-generation DOWN is injected after the initial neutral observation during a 250 ms horizon; the observer reads it back. The operation stays UNKNOWN, `release_confirmed=false`, task success null, replay denied, and admission for a new generation is refused both during and after uncertainty. This is stronger than the public stdio mock positive control: the supervisor detects a late old input and fails closed. It still does not show safe exclusion of every delayed operation or native Win32 device behavior.

## Interpretation and scope

This current-main synthetic protocol path does show the evidence shape required to accept recovery: separate source/recovery generations, a scoped neutral readback, finite post-release observations, exact operation identity, and refusal when the claimed horizon lacks enough observations. That is materially stronger than the X11 cancel worker's empty readback stage receipt, which cannot establish X server queue drainage or owner-exclusive state.

These results do not establish native Win32 physical input release, native MAP01 or another application's task effect, product-level recovery reliability, matched efficiency, or research-preview graduation. Keep those gates open and keep the test-fixture provider/backend distinction explicit.

Issue #57 evidence comment: https://github.com/Unjuno/agent-interface/issues/57#issuecomment-7056093106

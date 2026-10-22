# Win32 operation-owner implementation plan

Status: Phase 1's inert prototype is implemented and passes its scoped local
suite. Phase 2 has a partial target-generation prerequisite in the private
Win32 move bridge; public standard-caller/supervisor composition is not
implemented or qualified. This plan follows the
design decision in [the supervisor design record](PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md).
It authorizes only local inert-fake work in Phase 1; it does not authorize
native input or a WSLc allocation.

## Problem and scope

The current `Win32RuntimeSession.dispatch()` and `Win32Backend.execute()` call
`SendInput` synchronously. Existing fault-injection packets show that the
session can have no recorded release obligation while a fake `SendInput` has
already accepted DOWN and has not returned. A second schedule shows that
issuing UP from another sender before the original producer retires permits a
late DOWN. These are fake schedules, not observations of Windows behavior.

The current owned-process/supervisor path is X11-specific: it requires
`guarded-x11`, publishes X11 key/button obligations, and defaults to
`x11_cancel_worker`. Do not route Win32 through that worker. This plan evaluates
a separate Win32 operation owner while preserving the existing public caller's
target-generation checks, bounded cancellation response, UNKNOWN result,
no-replay rule, and opt-in default.

## Required state and ordering

One parent-side supervisor owns the operation ID, target generation, deadline,
admission fence, process handles, and cancellation result. A disposable child
per input program performs the admitted operation. The supervisor must:

1. Reject stale operation IDs, stale target generations, expired deadlines,
   duplicate admission, and any new operation while the prior producer's
   retirement is unresolved.
2. On cancel/expiry, close admission first, request child retirement, and wait
   only to a fixed bound. A timeout or lost IPC receipt is `UNKNOWN`; it is not
   proof of producer retirement and never permits a second input sender.
3. Attempt compensating UP only after the exact operation child is confirmed
   retired, using a separately bounded recovery process and only the frozen
   obligations for that operation.
4. Read key/button state through an independent, bounded observer. A missed
   readback, failed recovery, or ambiguous process retirement remains
   `UNKNOWN`, denies replay, and keeps input fenced.
5. Record task effect separately. A fresh target must pass an independent task
   oracle before the new task can be called successful.

Confirmed child exit is only a producer boundary. It does not prove that an
already accepted Windows input event was removed from an OS queue or cannot
take effect later. The late-DOWN horizon test below is therefore a mandatory
native gate; no code path may promote the synthetic model result to release
confirmation.

## Work sequence

### Phase 1: inert process/API model

Implement a spawn-safe, dependency-injected process-owner prototype and tests.
Use shared test state only; do not instantiate `Win32Backend`, call `user32`,
or emit desktop input. Force the producer to block both before fake acceptance
and after accepting DOWN but before returning. Exercise cancel, deadline,
retirement timeout, IPC loss, recovery-process failure, observer timeout,
stale operation ID/generation, repeated cancel, and attempted overlapping
dispatch.

The fake acceptance criteria are: caller response respects the declared bound;
no recovery UP is emitted before confirmed producer retirement; unresolved
retirement never admits another producer; old operation IDs cannot authorize
effects; and every uncertain branch returns UNKNOWN with replay denied. Run
focused tests normally and under `python -O`. Label all outputs synthetic.

An additional candidate packet now tests a prestarted-helper variant. Recovery
and observer helpers start and report ready before producer admission; cancel
reuses those processes and waits for a distinct completion receipt from the
helper's target function. Its focused suite passes 14/14 in normal and
optimized CPython 3.11.9. The packet is in
[`win32_prestarted_helper_experiment_20261022_r01`](../../research/integration/win32_prestarted_helper_experiment_20261022_r01/README.md).
This narrows only the fake cancel-path process-start gap: initialization can
still block while starting helpers, producer startup in `begin()` remains
synchronous, and termination, scheduling, IPC delivery, OS input release,
task effect, and native boundedness are unqualified. Treat this as a candidate
model, not a replacement for the frozen baseline or evidence of release.

### Phase 2: current-main composition

Only after Phase 1 passes, connect the opt-in owner to the standard guarded
caller through an explicit Win32 adapter. The private `MoveBridge` now pins a
digest of the HWND owner's PID and process creation time in its observation
binding and refuses if that generation cannot be queried or changes before
bound input. This is only a target-generation prerequisite: `mcp_server`
still has no guarded-Win32 route, `MoveBridge` still executes synchronously,
and neither is connected to the inert operation owner. The remaining Phase 2
gate is an explicit opt-in standard-caller adapter with executable composed
tests for target-generation change after model wait, cancellation while a
child is blocked, bounded caller response, separate effect scoring, exact
attempt accounting, and preservation of the completed prefix. Keep X11 worker
selection unchanged and fail closed if the selected backend and recovery
adapter disagree. Do not change the default backend or report a live release
result from these tests.

#### Approved implementation slice and file boundaries

The next implementation slice is a **synthetic-only public-caller composition**.
It does not enable native input, claim bounded release, or touch the WSLc
allocation. Implement in this order, stopping on the first failing invariant:

| Step | Intended code boundary | Required result |
| --- | --- | --- |
| 2a. Owner contract | New `runtime/guarded_win32_v1/operation_owner.py`; keep the inert research prototype as immutable evidence, not imported runtime code. | A spawn-safe parent owner admits one operation ID and immutable target-generation digest; owns monotonic operation/deadline state; closes admission before cancellation; treats missing/late receipts as UNKNOWN; does not launch compensating input while producer retirement is unresolved. Inject process factory, clock and observer so unit tests cannot reach native APIs. |
| 2b. Caller adapter | New `runtime/cli_v1/owned_win32_session.py`, implementing the narrow owner/session operations consumed by `register_guarded_tools`; do not subclass or select the X11-specific `OwnedGuardedSessionOwner`. | Retain original action and cancellation as separate records; preserve pending/terminal retrieval through `interface_results`; cancellation returns within the caller bound while its one owner operation retains custody; fresh operation IDs never mutate old UNKNOWN receipts. |
| 2c. Explicit route | `runtime/cli_v1/mcp_server.py` plus its focused tests. Add an opt-in `guarded-win32` route with explicit Windows-target construction and dependency-injected owner factory. Keep `guarded-x11`, its XRes worker selection and defaults byte-for-byte behaviorally unchanged. Reject the route on non-Windows hosts or invalid HWND/owner identity before admission. |
| 2d. Composition and regression | New focused caller-composition tests beside `runtime/cli_v1/test_mcp_owned_process.py`; retain bridge checks in `runtime/guarded_win32_v1/test_compiled_core_composition.py`. | Drive a changed target generation during model wait, blocked child cancellation, delayed/lost IPC, overlapping dispatch, recovery failure, observer timeout, and a distinct fresh target. Assert returned MCP receipt, child lifecycle, fake input log/state, separate effect oracle, exact attempt count and completed prefix. Run normal and `python -O`; rerun existing Win32 and X11 owner tests locally. |

The 2a local implementation now has a parent-side custody gate in
`runtime/guarded_win32_v1/operation_owner.py` and an opt-in inert process
lifecycle controller in `process_cancellation.py`. The gate retains the exact
producer handle and PID/creation-time identity; cancellation closes admission;
recovery can be claimed only after matching producer exit and before the
cleanup deadline. The controller returns a pending receipt without waiting
for child retirement, terminates only the retained producer, starts a separate
recovery process behind a parent-controlled start gate, verifies its identity,
and accepts only a matching operation/generation/recovery receipt followed by
neutral readback from a separately bounded observer child. Both children are
identity-checked and use the same absolute deadline with time reserved for
terminate/kill/reap. An unresolved producer, recovery child, receipt or
observer stays UNKNOWN, with replay denied and task success unset. Its tests
cover duplicate cancel, cancel-before-producer-registration, blocked recovery
and blocked observer; the focused spawned-process suite passes 4/4 in normal
and optimized mode. The owner suite passes 7/7 in both.

This validates only Python process ordering with inert shared test state. The
recovery/observer factories, native input adapter, public MCP caller, task
oracle and real Windows `SendInput` behavior are not integrated or qualified.
Child termination does not retract an already accepted OS input event and
neither helper scheduling nor native effect is a hard real-time bound.
Continue 2a with adversarial IPC, deadline, identity and observer failure cases
before caller composition; do not count these tests as evidence of bounded
input release.

Do not solve a blocked native call by calling `release_all()` from a second
thread/process while the original producer may still emit input. The owner must
establish producer retirement before any compensating sender is admitted. If
the process boundary cannot safely contain a blocked `SendInput`, the composed
result stays UNKNOWN and the route remains opt-in/disabled pending the native
gate. Do not reinterpret a fake observer or a bridge-local effect callback as
an independent application oracle.

The caller integration is accepted only when all step 2d assertions pass on
the same frozen source and the existing guarded-X11 regression suite remains
green. This is a plan gate, not evidence that steps 2a–2d have been implemented.

### Phase 3: isolated native discriminator

Before native input, require an identified disposable Windows target, a
separate output location, a reviewed stop/cleanup procedure, independent
platform-state observation, and a verified exclusive allocation. Run the
before-acceptance and after-acceptance schedules; after confirmed child exit
and recovery UP, observe through a declared horizon for any late DOWN. Then
verify a fresh target's independent task effect. Preserve all first outcomes.
If the target, ownership, observer, or stop path is unavailable, do not run;
keep the result UNKNOWN. This plan grants no WSLc access and does not override
Issue #7924 STOP.

### Phase 4: standard-caller qualification

Only if both native schedules establish the producer fence, bounded neutral
state, and late-DOWN absence should the adapter enter a matched comparison.
Freeze baseline, task order, model/settings, all-attempt usage accounting,
latency endpoints, repair policy, repetition count, and stopping rule before
seeing results. Report task correctness, collateral effects, release
confirmation coverage, late inputs, uncertainty, model usage, and full time to
independent task effect. A negative or inconclusive result completes this
qualification attempt and does not authorize automatic adoption.

## Rejection conditions

Reject or keep disabled if an old DOWN can occur after retirement and recovery,
if process retirement/readback is unbounded, if any unresolved producer
overlaps a recovery sender, if target-generation checks can be bypassed, or if
the task effect cannot be independently verified. A bounded caller response
with UNKNOWN is useful containment, but it does not satisfy bounded release.

## First deliverable

Phase 1's baseline tests and local receipts are retained in the [R01 prototype
packet](../../research/integration/win32_operation_owner_prototype_20261022_r01/README.md).
The r01 attempt records one test expectation failure; r02 passes 12/12 in
normal and optimized CPython 3.11.9. The separate prestarted-helper candidate
passes 14/14 in both modes; its raw output and conditions are retained in its
packet. These are synthetic process-ordering results only.
The current fake Win32 packets remain immutable and are the baseline
counterexamples. Phase 2 composition, native qualification, matched
efficiency, and reliability remain open.

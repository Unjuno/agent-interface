# Win32 operation-owner implementation plan

Status: Phase 1 and Phase 2's synthetic-only public MCP composition are
implemented on current main. The route binds/rechecks an injected target
generation, admits a gated synthetic producer, composes cancellation with
separate recovery and neutral-state observation, and retains an independently
spawned task-effect oracle receipt. This does not qualify native input or
physical release. This plan follows the design decision in [the supervisor design
record](PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md). It authorizes local
synthetic-fake work only; it does not authorize native input or a WSLc
allocation.

Current-main addendum (2026-10-24): the public MCP/backend composition suite
now verifies a mismatched recovery receipt remains UNKNOWN through
`interface_results`, does not start the observer, and cannot promote release
or task success. A target-incarnation property/query failure during admission
is normalized to `TARGET_GENERATION_CHANGED`. The [R01 packet](../../research/integration/win32_public_recovery_unknown_20261024_r01/README.md)
records 51 focused public-caller, backend, owner, and supervisor tests passing
in normal and optimized Python. This closes one public failure-path test gap;
the live native producer/recovery composition and Phase 3 discriminator remain
unqualified.

Current-main continuation (2026-10-24): PR #9460 makes admission refusal while
an earlier producer remains unresolved machine-readable at the public
boundary. A second admission returns `blocked` / `INPUT_PRODUCER_UNRESOLVED` with the prior
operation ID and does not create a call or start another producer. Across the
public composition, backend composition, owner, and cancellation tests, the
Phase 2d synthetic failure matrix now covers target changes during waits,
blocked/cancelled start gates, delayed or missing helper receipts, overlapping
admission, recovery/readback failures, fresh-generation isolation, and exact
producer/oracle attempts. All 57 selected tests pass in normal and optimized
Python. This closes the synthetic Phase 2d test gap only.

The separate [R03 native packet](../../research/integration/win32_native_supervised_sendinput_hook_20261024_r03/README.md)
passes one finite schedule with a real hook-blocked F13 `SendInput`, exact
producer retirement, one same-generation recovery UP, independent readback,
and a 1.5 s horizon. R01/R02 are retained construction aborts. R03 does not
cover the required before-acceptance and after-acceptance pair, does not use
the public MCP caller, and has no task-effect oracle. It therefore does not
satisfy Phase 3. Issue #7924 remains OPEN/STOP/HOLD: the last WSLc run lacked
the pinned image, cleanup was unverified, and no unused slot is verified.
Do not run or wire native input on the strength of R03 alone.

## Current implementation checkpoint (2026-10-23)

The local branch `codex/win32-supervisor-implementation-plan` now implements
the approved persistent-helper candidate and extends the synthetic public
caller slice. `OperationCancellationSupervisor` starts one recovery and one
observer process before the first producer can be admitted, checks exact
readiness receipts and retained process identities, and reuses the helpers
through request/result/completion receipts. A missing, malformed, late, or
mismatched response keeps custody UNKNOWN; invalid helpers are retired and
never replaced during cancellation. The public caller retains one producer
start and one oracle reservation per call. A late Generation-A oracle success
cannot promote the earlier timeout, duplicate cancellation returns the same
attempt, and Generation B scores as a distinct attempt.

The new fake-API test dispatches through the actual `Win32RuntimeSession` and
`Win32Backend.execute()` paths. It covers blocked-before-acceptance and
accepted-before-return schedules plus producer-retirement timeout. The
process-shared fake key state and parent event log show confirmed exact
producer exit before the fake backend recovery UP; an independent helper then
reads neutral state. Timeout remains UNKNOWN and emits no recovery UP. No
production injection seam was required.

The source-bound [R01 custody packet](../../research/integration/win32_supervisor_custody_20261023_r01/README.md)
records 79/79 selected pure/fake tests and 67/67 MCP-owned-process/guarded-X11
compatibility tests passing in normal and optimized CPython 3.11.9, raw output,
conditions, source hashes, and an invalid native-test execution incident. The
native fixture integration class is excluded from valid verification. This
branch has no native `SendInput` adapter, physical
release proof, late-DOWN horizon, live MAP01 oracle, exclusive input
authority, matched efficiency result, or repeated reliability result. The
mechanism remains opt-in and synthetic only. Issue #7924 remains STOP/HOLD;
this work used no WSLc allocation or Docker.

## Problem and scope

### Joined public-caller/backend verification (2026-10-23)

The [joined-path R01 packet](../../research/integration/win32_public_backend_composition_20261023_r01/README.md)
closes the separate-test gap through the existing injected producer factory.
Three new tests drive public MCP bind/admit/start/cancel/results through the
actual Win32 session/backend with an inert API. Both blocked-DOWN schedules
record exact producer retirement before recovery UP and independent readback;
an unretired producer stays UNKNOWN with no UP. Duplicate public start/cancel
preserve one attempt, generation/operation links survive the full path, and
task success remains null. The 15 related tests pass normally and under `-O`.
A deliberately premature fake UP fails the ordering assertion.

This is test-only composition, not a production native-input adapter. The
public route still requires injected factories; live target identity, physical
release, task effect, timing, efficiency and reliability remain open.

The [closed-gate cancellation packet](../../research/integration/win32_unopened_gate_cancel_20261023_r01/README.md)
additionally reproduces a cancellation during the final generation query that
previously sent an UP despite the producer gate never opening. Public caller
admission now declares that a parent gate is required. The owner tracks closed
versus attempted authorization; retiring a known-closed producer stays UNKNOWN
without claiming recovery or emitting UP. Direct clients without a declared
gate remain untracked, not presumed closed. Native recovery-time authority
after authorized input is still an open qualification boundary.

### Platform call boundary

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

Historical checkpoint: the private `MoveBridge` pinned a digest of the HWND
owner's PID and process creation time and refused if that generation could
not be queried or changed before bound input. At that point there was no
guarded-Win32 public route and the synchronous bridge was not connected to the
inert operation owner. That gap is now closed for a synthetic-only slice:
`mcp_server` exposes an opt-in dependency-injected route, target generation is
rechecked before admission, cancellation composes spawned recovery and
independent neutral-state observation, and a distinct process can score task
effect. R04 also verifies that generation A remains UNKNOWN/replay-denied
while generation B succeeds as a separate public session. See the
[2026-10-23 implementation plan](../superpowers/plans/2026-10-23-win32-supervisor-custody-plan.md)
for the remaining failure-matrix, actual-backend-with-inert-API and exact
attempt-accounting work. Keep X11 worker selection unchanged and fail closed
if the selected backend and recovery adapter disagree. Do not change the
default backend or report a live release result from these tests.

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
cover pre- and post-acceptance blocks, duplicate cancel,
cancel-before-producer-registration, unretired producer, blocked recovery,
blocked observer, recovery identity mismatch, missing recovery IPC receipt and
wrong-operation receipt; the focused spawned-process suite passes 9/9 in normal
and optimized mode. The owner suite passes 7/7 in both.

The 2a inert process/custody crosswalk now covers before/after fake acceptance,
replay refusal, overlap refusal, cancellation during producer startup, blocked
recovery and observer, retirement failure, identity mismatch, missing IPC and
wrong-operation receipt. This validates only Python process ordering with
inert shared test state. It does not integrate the native input adapter, public
MCP caller, task oracle or real Windows `SendInput` behavior. Child termination
does not retract an already accepted OS input event and neither helper
scheduling nor native effect is a hard real-time bound. Do not count these
tests as evidence of bounded input release.

The current 2b adapter slice in `runtime/cli_v1/owned_win32_session.py` keeps
the original action record and cancellation transaction separate, reuses one
cancellation ID on duplicate requests, and exposes pending/terminal owner state
through its local `interface_result` seam. A callback-level regression passes
the adapter to `register_guarded_tools` and confirms that confirmed neutral
readback does not promote the action result or task success. This is not yet
wired to `mcp_server.create_server()` or its `interface_results` endpoint; that
public route/retrieval composition remains a required follow-up. The adapter
imports no Win32 backend and emits no input. Its focused suite passes 5/5 in
normal and optimized CPython; the existing MCP server/owned-process suites pass
76/76 in normal mode from the repository root.

Do not solve a blocked native call by calling `release_all()` from a second
thread/process while the original producer may still emit input. The owner must
establish producer retirement before any compensating sender is admitted. If
the process boundary cannot safely contain a blocked `SendInput`, the composed
result stays UNKNOWN and the route remains opt-in/disabled pending the native
gate. Do not reinterpret a fake observer or a bridge-local effect callback as
an independent application oracle.

The current-main synthetic public-caller slice now has the bounded 2d
failure-schedule and attempt-accounting matrix described above. Its tests do
not establish native release behavior. Phase 2 remains a synthetic contract;
Phase 3 requires an isolated allocation and the separately frozen native
before/after-acceptance discriminator with an independent task oracle.

#### Current-main regression recheck (2026-10-23)

The preceding status predates the [additive current-main R02 packet](../../research/integration/win32_public_backend_composition_currentmain_20261023_r02/README.md). On current main `4c0fe4d31`, 48 selected public-caller, backend-composition, operation-owner, and cancellation-supervisor tests pass in both normal and optimized Python. Eight retained traces independently confirm one producer attempt, exact target-generation and operation binding, retirement before synthetic recovery UP, observer ordering, and conservative UNKNOWN results for a closed start gate or unretired producer. The packet binds 13 source blobs and preserves both raw runs and traces. This rechecks the listed synthetic regression paths; it does not qualify native SendInput, physical release, a real task oracle, WSLc, matched efficiency, or reliability. Phase 3 remains gated on a verified isolated allocation and native discriminator.

PR #9435 adds `Win32Backend.target_generation()` as a reader suitable for `OwnedWin32SessionOwner.bind_target_generation_reader()`. Its SHA-256 input includes the configured HWND, GUI-thread ID, owner PID, and process creation time; the PID/TID association is sampled on both sides of the process-time query. A public `mcp_server.create_server()` regression changes only the GUI-thread ID after binding while keeping the HWND and process identity constant; admission returns `TARGET_GENERATION_CHANGED`, creates no operation record, and calls no producer factory. The backend, adapter, and public-server suites pass 25/25 in normal and optimized Python. APIs remain mocked. Same-numeric-HWND reuse on the same thread can alias; `mcp_server` still requires an explicitly injected synthetic-only owner/producer. Native input composition and Phase 3 remain open.

#### Live Win32 follow-up on the user-authorized PC (2026-10-23)

PR #9448 retains the R04 native fixture experiment: the existing operation owner and cancellation supervisor handled one pause before `SendInput` and one after the real API returned an accepted CTRL-down. Both schedules retired the exact producer, recovered CTRL-up, and passed a 1500 ms independent foreground/input-desktop observation; a fresh fixture then passed a public stdio-MCP task-effect check. Its independent packet audit passes 17/17. The pauses are outside the Windows API call, so this does not establish behavior when `SendInput` itself is blocked.

The [R03 public live-generation packet](../../research/integration/win32_public_live_generation_20261023_r03/README.md) then used real `Win32Backend.target_generation()` reads for two owned HWND generations through the registered `mcp_server.create_server()` guarded-Win32 tools. After Generation A was admitted and the current target changed to Generation B, the public start handler returned UNKNOWN before invoking its injected producer factory; `interface_results` retained UNKNOWN, the producer gate stayed closed, and task success/replay remained denied. Its independent audit passes 8/8. The calls used in-process `server.call_tool`, and no input was emitted. R01 exploratory and R02 harness-failure records remain preserved.

These samples strengthen native-state and public target-generation evidence separately. They do not join native producer/recovery with the standard public caller. `mcp_win32` still labels its route synthetic-only and `mcp_server.create_server()` requires an injected synthetic owner/producer. Do not wire a native producer into this route until Phase 3 proves both native acceptance schedules, bounded neutral readback, late-DOWN absence, and independent task success on a verified isolated allocation. Preserve UNKNOWN, generation binding, and retirement-before-recovery in that future composition. Issue #7924 remains STOP/HOLD; Docker is unused.

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

# Win32 Prestarted Supervisor for Bounded Input Recovery

**Status:** Design proposal for review
**Scope:** Win32 input-operation ownership and bounded recovery
**Decision requested:** Approve, revise, or reject the proposed falsifiable prototype before a separate implementation plan is written.

## Context and outcome

The required outcome is a bounded cancellation response **and** bounded input neutralization while an input API call is blocked, followed by independent platform-state readback and an independently checked task effect on a fresh target. A bounded return by itself is not release. Until each property is observed, the operation result remains `UNKNOWN`, replay is denied, and no new input operation may overlap a producer whose retirement is unresolved.

Current `Win32RuntimeSession.dispatch()` and `Win32Backend.execute()` call `SendInput` synchronously. The backend records a held-key obligation only after `SendInput` returns; `recover_input()` refuses before attempting release unless `recovery_required` is already true. The accepted-before-return packet and the later [before-acceptance public-recovery packet](../../research/integration/win32_before_accept_blocked_recovery_20261022_r01/README.md) both reproduce blocked-call schedules with an inert fake: bookkeeping says recovery is unnecessary, public recovery refuses without UP, and the old producer can still accept DOWN after recovery returns. The latter confirms the source-derived schedule for that test double; neither packet is a captured native Windows outcome.

Microsoft documents `SendInput` as inserting events serially and returning the inserted count. Its documented signature exposes no deadline or cancellation handle. That documentation does not establish whether process termination prevents an already accepted event from taking effect later. Microsoft also documents `TerminateProcess` as asynchronous and requires waiting on the process handle to confirm exit; the documentation does not establish whether an in-flight `SendInput` maps to pending I/O for its termination rule. These uncertainties remain explicit test gates.

## Candidate design

A prestarted supervisor is the sole parent-side owner of operation state. For each bounded input operation it creates a disposable child that performs at most one admitted program and reports through bounded IPC. The child must complete a bounded readiness handshake before the supervisor admits the operation; no input is sent if process creation, identity binding, or readiness times out. On cancellation or expiry, the supervisor stops admitting work, retires that exact child, and waits only until a fixed deadline. It records retirement as confirmed or unknown.

A distinct, prestarted recovery process may submit compensating UP events only after the operation producer's retirement is confirmed. An independent observer then reads key and button state. If retirement or readback misses its bound, the supervisor returns `PENDING` or `UNKNOWN` to the caller within its response budget, denies replay, and keeps new input fenced. This response is not proof of release; if the caller's required outcome is confirmed neutralization by that budget, the candidate fails qualification. A bounded caller response never authorizes another sender while the prior producer remains alive or its retirement is unknown.

This boundary is a candidate, not a qualified architecture. Process retirement may stop future user-mode submissions without proving that an already accepted event cannot take effect later. The prototype must therefore include a late-DOWN discriminator: exercise calls blocked both before and after acceptance, retire the producer, attempt recovery only after the ownership boundary, and observe whether any DOWN appears after the accepted recovery point through a declared horizon.

## Alternatives

1. **Recovery thread in the existing process — reject for bounded release.** It cannot preempt a synchronous caller or fence late producer work. The R01 probe also shows public recovery can refuse while the modeled key is held.
2. **Prestarted supervisor with disposable operation and recovery processes — preferred falsifiable prototype.** It provides an observable producer-retirement boundary and keeps a bounded caller-response path. It is acceptable only if both admission schedules pass, including native late-DOWN observation and independent readback.
3. **Target-specific API with server-side generation and expiry — preferred production route where available.** It can bind authorization and effect to target state, but is not a general desktop backend and needs separate integration and effect evidence.

Reject the supervisor prototype if an old DOWN can arrive after confirmed child retirement and recovery, if release state cannot be independently observed, or if a fresh target's task effect cannot be checked.

## State and failure semantics

- Only the supervisor admits an operation and owns its identity, deadline, child identity, and recovery state.
- The supervisor binds the child to one operation identity and waits for readiness before admitting input. Cancellation first closes admission for that operation, then requests child retirement.
- Child retirement is `CONFIRMED` only after the exact child process handle is signaled within the configured bound. Timeout, lost IPC, or ambiguous identity is `UNKNOWN`.
- Recovery cannot start while the producer may still emit. A refusal or timeout is not release confirmation.
- Independent state readback is a separate observation with its own deadline and raw evidence.
- Any unresolved producer, failed recovery, or unavailable observer leaves the result `UNKNOWN`, denies replay, and keeps new input fenced.
- A task is successful only when a fresh target's effect is checked independently from the input sender's receipt.

## Validation gates

1. **Inert state-machine tests:** cover process/readiness timeout before admission, blocked-before-acceptance and accepted-before-return, child-retirement timeout, IPC loss, recovery-owner failure, stale operation IDs, repeated cancellation, and prevention of overlapping producers. Run focused tests normally and with Python optimization enabled.
2. **Platform semantics review:** check process and input-queue behavior against primary Windows documentation. If accepted-event cancellation remains unspecified, keep the native safety claim open.
3. **Isolated native discriminator:** only with a verified disposable target, exercise both schedules and preserve OS/process identities, timing bounds, raw event and independent-state observations, late-DOWN horizon, and independent task effect. No desktop-wide input is implied.
4. **Standard-caller integration:** begin only after the ownership protocol passes. Then run matched baseline/recovery measurements for response latency, release-confirmation coverage, late-input count, and task correctness. Reliability needs independent repetitions under a predeclared policy.

## Explicit non-goals and current evidence

This design does not claim bounded release, Windows qualification, successful task effect, matched efficiency, or reliability. It does not authorize runtime implementation, native-input execution, WSLc/Docker use, or a new allocation. The current result remains `UNKNOWN`.

The existing Win32 evidence checkpoint and synthetic schedule are recorded in [`docs/architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md`](../../architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md), including the limitations of the R01 fake API result. This standalone specification makes the candidate and its falsification gates reviewable; it does not replace that evidence record. The historical Xvfb specification at this directory's `2026-10-22-prestarted-cancel-supervisor-design.md` is preserved independently and covers a different route.

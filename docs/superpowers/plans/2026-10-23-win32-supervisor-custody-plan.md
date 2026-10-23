# Win32 Supervisor Custody Completion Implementation Plan

> **For agentic workers:** Execute task-by-task and keep each task's evidence separate. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the already-tested prestarted-helper model into the Win32 operation owner, then verify its public-caller and actual-backend composition while preserving bounded custody, distinct attempts, and immutable UNKNOWN outcomes.

**Architecture:** Keep the parent-side `Win32OperationOwner` as the sole custody authority. Change `OperationCancellationSupervisor` to start recovery and observer helpers and verify readiness before any operation can be admitted; cancel then reuses those helpers instead of starting processes. Compose that lifecycle through the guarded-Win32 public caller and actual `Win32RuntimeSession`/`Win32Backend` with an inert fake API only. Native qualification remains a separate gate.

**Tech Stack:** Python 3.11+, `unittest`, multiprocessing `spawn`, asyncio MCP route, injected clocks/process factories/observers, fake Win32 API.

**Spec:** [Prestarted cancellation supervisor design](../../architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md), especially “Candidate ownership boundary,” “Options and decision,” and “Validation sequence and remaining gates.” Existing caller slice and non-goals: [Win32 operation-owner implementation record](../../architecture/WIN32_OPERATION_OWNER_IMPLEMENTATION_PLAN.md).

## Global Constraints

- Keep guarded Win32 opt-in and synthetic-only until separate native gates pass.
- Never send compensating UP until the exact producer is confirmed retired and its operation/generation identity matches.
- Missing, late, malformed, or mismatched receipts stay `UNKNOWN`; replay stays denied and admission remains fenced.
- A fresh generation is a distinct attempt and must not mutate any previous generation's result.
- Task effect, cancellation/recovery, neutral-state observation, and caller response remain distinct evidence.
- Do not call native `SendInput`, control a physical desktop, use WSLc/Docker, or claim bounded release from fake tests.
- Preserve existing guarded-X11 behavior and run its relevant regression suite after public-caller changes.

## Review Focus

- Recovery or observer helper startup/readiness fails: admission must remain closed and no producer may start.
- A helper dies or loses its receipt after admission: result remains UNKNOWN, admission stays fenced, and cancel creates no replacement helper.
- Cancel races with producer registration or start authorization: the late child must remain gated and unable to act.
- A recovery receipt for another operation/generation or a helper identity mismatch: no release confirmation and no admission reopen.
- A caller timeout followed by late producer/oracle completion: the retained terminal outcome must not be promoted or replaced.
- Fresh target recovery: the new attempt may score independently while the old attempt remains immutable UNKNOWN.
- Repeated start/cancel/oracle requests: exact-once attempt accounting and stable retrieval without implicit replay.

---

### Task 1: Reuse prestarted recovery and observer helpers in the runtime owner

**Files:**
- Modify: `runtime/guarded_win32_v1/process_cancellation.py`
- Modify: `runtime/guarded_win32_v1/test_process_cancellation.py`
- Reference: `research/integration/win32_prestarted_helper_experiment_20261022_r01/operation_owner.py` (read from committed Git blob if omitted by the sparse checkout)

**Interfaces:**
- Consumes: existing `OperationOwner`, recovery/observer process factories, process identity reader, and absolute cleanup deadline.
- Produces: supervisor construction starts and verifies exactly one recovery helper and one observer helper before operation admission; accepted cancellation reuses them and starts no helper process. Failed startup/readiness prevents producer admission. A timed-out or lost helper is retired or marked unavailable, returns UNKNOWN, and is never silently replaced during cancel.

- [x] **Step 1: Add failing process-count/readiness tests** for normal startup, factory startup exception, malformed observer readiness, and helper death during a request. Assert construction fails unless both helpers provide valid ready receipts.
- [x] **Step 2: Add failing cancel-order tests** asserting that the pre-admission process count is unchanged by cancellation, no UP precedes exact producer retirement, one request/complete receipt pair is required per reused helper, and a failed helper cannot authorize a new sender.
- [x] **Step 3: Run the new tests** with `python -m unittest runtime.guarded_win32_v1.test_process_cancellation -v` and verify failures are on process count/readiness/order rather than fixture setup.
- [x] **Step 4: Implement helper startup, readiness, request serialization, receipt validation, and deterministic close** in `OperationCancellationSupervisor`. Keep creation synchronous before admission; do not claim a server-start deadline from this work.
- [x] **Step 5: Run the full process-cancellation and owner suites** normally and under `python -O`; verify helper creation occurs only before producer admission and that cleanup handles all startup-failure paths.
- [x] **Step 6: Commit** the runtime lifecycle and its tests as one reviewable change (`d43b84be5`).

### Task 2: Close the public-caller custody failure matrix

**Files:**
- Modify: `runtime/cli_v1/test_mcp_win32_composition.py`
- Modify only if a failing regression demonstrates a defect: `runtime/cli_v1/mcp_win32.py`, `runtime/cli_v1/owned_win32_session.py`

**Interfaces:**
- Consumes: `register_guarded_win32_tools(server, owner, content, *, producer_factory, task_oracle=None)` and the owner methods `bind_target_generation`, `admit_action_from_binding`, `start_producer`, `cancel_action`, `interface_result`.
- Produces: public receipts that preserve helper custody, action/cancellation/recovery/observation/effect separation, attempt count, target generation, and replay denial.

- [x] **Step 1: Add named public-route regressions** for observer timeout, repeated cancel, duplicate start, oracle timeout followed by late success, and mismatched recovery operation/generation; lower-level process tests cover missing/malformed recovery receipts. Assert immutable `UNKNOWN`, `task_success is None`, `replay_allowed is False`, and one producer/oracle reservation.
- [x] **Step 2: Run the new tests** with `python -m unittest runtime.cli_v1.test_mcp_win32_composition`; all observed behaviors matched the required invariants.
- [x] **Step 3: Make the smallest caller/owner changes** needed to satisfy those assertions. No caller/owner change was required; the route already enforces the tested behavior.
- [x] **Step 4: Re-run the focused suite** normally and under `python -O`; both runs passed and the generation-A immutability regression remained green.
- [x] **Step 5: Commit** the tests as one reviewable custody change (no runtime correction was needed; commit `7dfea017b`).

### Task 3: Prove process custody through the actual Win32 session/backend with an inert API

**Files:**
- Create or extend: `runtime/backends/win32_v1/test_supervised_session.py`
- Modify only if needed to expose an injection seam: `runtime/backends/win32_v1/session.py`, `runtime/backends/win32_v1/backend.py`, `runtime/guarded_win32_v1/process_cancellation.py`
- Reference tests: `runtime/backends/win32_v1/test_release_ledger.py`, `runtime/backends/win32_v1/test_explicit_up_ledger.py`, `runtime/guarded_win32_v1/test_process_cancellation.py`

**Interfaces:**
- Consumes: `Win32RuntimeSession.dispatch()` and `Win32Backend.execute()` with a fake `user32.SendInput`; process ownership and receipt protocol from Task 1's existing supervisor.
- Produces: a deterministic composed test trace for block-before-accept and accept-before-return schedules; no exported API change is allowed unless a current interface makes dependency injection impossible.

- [x] **Step 1: Add two spawned-process tests** that invoke the actual session/backend using only a fake API: (a) DOWN is blocked before acceptance, and (b) DOWN is accepted into fake state before the call blocks. Keep the fake API state in process-safe test storage and record event order.
- [x] **Step 2: Assert the custody order**: cancellation closes admission; the fake event log contains no recovery UP before exact producer exit; a retirement timeout yields UNKNOWN and blocks a second dispatch; confirmed retirement permits only the matching recovery receipt and independent fake neutral-state readback.
- [x] **Step 3: Run the tests** normally and under `python -O`; check process cleanup in `finally` paths and ensure the tests fail if recovery is moved before producer exit.
- [x] **Step 4: No construction seam was needed**: the test creates `Win32Backend` via `__new__` and assigns a fake `user32`; production construction remains unchanged.
- [x] **Step 5: Re-run Win32 pure helper, backend ledger, owner, process-cancellation, and public-route tests** in both modes. The native fixture integration class was excluded from the valid verification set.
- [ ] **Step 6: Commit** the isolated actual-backend/fake-API composition test.

### Task 4: Make attempt accounting and retained evidence auditable

**Files:**
- Modify: `runtime/cli_v1/test_mcp_win32_composition.py`
- Modify: `runtime/cli_v1/test_attempt.py` only if the existing attempt ledger cannot express the assertions
- Create: `research/integration/win32_supervisor_public_attempts_<date>_r01/README.md`, `conditions.json`, `SHA256SUMS`, and raw normal/optimized outputs
- Update after results: `docs/CURRENT_GOAL.md`, `docs/architecture/WIN32_OPERATION_OWNER_IMPLEMENTATION_PLAN.md`

**Interfaces:**
- Consumes: public MCP call IDs, frozen action operation IDs, generation-bound owner receipts, and independent oracle receipts.
- Produces: a retained row per attempted action/cancel/recovery/observer/oracle phase, including pending/unknown outcomes, exact invocation count, and a content-addressed source/result packet.

- [ ] **Step 1: Add an accounting regression** that submits one action, repeats retrieval/cancel, times out the oracle, supplies a late receipt, and starts a separate fresh generation. Assert exactly one producer start and one oracle reservation per original call; retrieval and duplicate requests do not create attempts; the old result remains byte-for-byte equivalent after the new generation succeeds.
- [ ] **Step 2: Run the regression** normally and under `python -O`; require exact attempt totals and old-generation immutability.
- [ ] **Step 3: Capture the complete focused test commands, exit codes, Python/platform versions, source revision, and raw outputs** into the new packet. Hash source files and all packet files; do not edit prior R01–R04 packets or the prestarted-helper R01 packet.
- [ ] **Step 4: Update the architecture checkpoint and current-goal summary** with only the observed synthetic result, exact local test counts, and remaining qualification boundary.
- [ ] **Step 5: Run `git diff --check`, the focused Win32 suite, the existing MCP-owned-process/guarded-X11 regression suite, and the relevant backend/owner suites** in normal and optimized modes; preserve failures as well as passes.
- [ ] **Step 6: Commit** the test, packet, and concise status updates together after verifying every recorded hash.

## Explicit later gates (not part of this implementation plan)

This plan does not authorize native desktop input or a WSLc allocation. Before any native experiment, a separate review must verify a disposable target, unique active allocation, exclusive input authority, independent state observer, stop/cleanup procedure, declared late-DOWN horizon, and independent task oracle. Native late-DOWN absence, fresh-target recovery, matched efficiency, and repeated reliability remain open until separately executed and recorded. No fake process result may be promoted into a native release claim.

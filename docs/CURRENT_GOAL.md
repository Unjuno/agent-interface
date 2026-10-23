# Current objective and working direction

**Public stdio MCP Win32 artifact integration blocker (2026-10-23):** live R01 used the actual `mcp_server` stdio client and an owned fixture, but public observe/dispatch stopped before `session.dispatch` because `api.py` requires `configure_capture_artifacts` and Win32 lacked it. The fixture recorded no character/save event, no effect file, and no release attempt; preserve this as failure, do not retry R01. Win32 exact-capture PNG artifact support is added locally with 27 focused tests passing in normal/`-O`; a fresh R02 is needed to verify the repaired public path. See the [R01 packet](../research/integration/win32_public_mcp_live_effect_20261023_r01/README.md). This does not establish generation admission, blocked-I/O release, recovery, MAP01, or efficiency.

**Native Windows target-identity smoke (2026-10-23):** the [R01 packet](../research/integration/win32_native_target_identity_20261023_r01/README.md) exercises production `Win32Backend.process_identity()` and `target_generation()` against one hidden HWND created and destroyed by the probe on this PC. The real Win32 API returned stable PID/process-creation identity and generation across repeated reads; the owned HWND was absent after destroy. Its 8-check raw audit and 12 focused tests in normal/`-O` modes pass. An initial import-path setup error is preserved. This qualifies only native identity API wiring for one live HWND; no input, release, target-reuse detection, task effect, recovery, WSLc, or efficiency claim.

**Native HWND reuse discriminator (2026-10-23):** the [R01 one-shot packet](../research/integration/win32_hwnd_reuse_20261023_r01/README.md) created and destroyed two hidden `STATIC` windows sequentially on the same thread, using production owner-identity and generation methods. Windows returned different numeric HWNDs (`50923368`, `50988904`), so the result is `NO_REUSE_OBSERVED_IN_THIS_SINGLE_TRIAL`; both windows were destroyed and the 7-check receipt audit passes. This is inconclusive about reuse/aliasing and was not retried. It adds no input, release, effect, recovery, MAP01, or efficiency qualification.

**Real terminal saved-effect task (2026-10-23):** the [frozen rootless xterm trial](../research/integration/xterm_public_task_20261023_r01/README.md) uses public guarded MCP to type a known command through actual xterm/PTY/shell, producing exactly one independently read/fsynced record with owned ancestry.14 pre-frozen-auditor checks pass; source/native binaries and cleanup retained. Input returns65.438ms after invocation, saved effect commits72.876ms after invocation, so API completion precedes task commit by7.437ms in this sample. Custom record helper, one known zero-model task, no fault/comparison; no general terminal/Calc/MAP01 or efficiency/reliability claim. Setup is user-cache extraction only, not system installation or WSLc.

**Queued-UP boundary and interpretation correction (2026-10-23):** [two new frozen cases](../research/integration/x11_queued_up_cancel_20261023_r01/README.md) record target UP queued after the delayed XTEST request and before real sync. Without server pause: old counted task PASS/count1 and fresh PASS; with1000ms pause: old FAIL/count3, fresh PASS. Both preserve UNKNOWN/no replay and pass28 raw checks each. Earlier descriptions of the old task as an “explicit held-key” operation were incorrect: it is `key_chord`, stalled behind the injected delayed request. The new packet supersedes that interpretation without rewriting old raw/results. Completion-hold comparison #9427 remains valid for its distinct after-reply hook. No hard deadline, physical/MAP01, efficiency or reliability claim.

**Matched completion-hold discriminator (2026-10-23):** a [frozen ABBA public-guarded comparison](../research/integration/x11_tap_completion_hold_20261023_r01/README.md) uses identical current caller/guards with prior vs repaired key methods. During a one-second completion hold after a real X sync reply, both prior cases remain DOWN/count10; both repaired cases are UP/count1. All four end neutral; 47 pre-frozen-auditor checks pass. This qualifies that client-facing completion boundary only, not network reply loss, blocked send, stopped server, supervisor cancellation, general exactly-once effects, MAP01, efficiency or broad reliability.

**Single-key chord reply-boundary repair (2026-10-23):** the [backend repair](../research/integration/x11_single_tap_reply_boundary_20261023_r01/README.md) queues eligible single-key DOWN/UP before one final key-state reply, retaining subclass guards and possible-DOWN custody. 143 related pure tests pass normal/-O. A [fresh native public-caller run](../research/integration/x11_single_tap_live_20261023_r01/README.md) passes 24 raw checks and fresh count `[0]→[1]→[1]`; old explicit held-key count `[1]→[3]` remains task FAIL/UNKNOWN. This removes an avoidable reply wait, not stalled-write/queue atomicity or held-key repetition. No measured speedup, physical/MAP01, efficiency or reliability claim.

**Counted task-oracle repair and live verification (2026-10-23):** the [repair](../research/integration/xvfb_effect_count_oracle_20261023_r01/README.md) adds strict non-idempotent effect counts to the blocked-release fixture; 20 pure tests pass normally and under `-O`. A [new frozen native Xvfb run](../research/integration/xvfb_counted_effect_local_20261023_r01/README.md) independently reads old count `[1]→[4]` with unchanged value `[1]`, correctly scoring old task FAIL; fresh count `[0]→[1]→[1]` scores PASS. The 24-check raw audit and owned-process cleanup pass, while old runtime UNKNOWN/no-replay remains. This repairs observability, not old repeated effects or general exactly-once semantics. Other server-stop legacy scorers remain value-only; no WSLc/physical/MAP01, efficiency or reliability claim.

**Paused local caller trial and oracle counterexample (2026-10-23):** [R01](../research/integration/xvfb_blocked_release_local_20261023_r01/README.md) passed its single existing Xvfb test: cancel response 254.184 ms, post-resume all-up, fresh-target effect `[0]→[3]` with 89.901 ms input-to-independent-readback, old UNKNOWN/no-replay preserved. The separate 20-check raw audit also found three old-window KeyPress/effect handlers masked by idempotent `[1]` assignment, so the scorer's literal “one initial effect” is unproven/contradicted at event level. Next: explicit non-idempotent effect-count fixture/oracle and duplicate-event regression; preserve this result. Native WSL2 only, no WSLc/Docker or Windows desktop input; no efficiency/reliability/MAP01 claim.

**Local observation prerequisite (2026-10-23):** the [public MCP observation R01 packet](../research/integration/xvfb_public_observation_20261023_r01/README.md) records one new authenticated private Xvfb, two exact 64×64 fixture images, retained-image identity, timestamp ordering and clean close/exit; 19 offline raw-reconstruction checks pass. This qualifies the newly prepared local WSL2 observation environment only. No input, WSLc allocation, input-caused task effect or performance/reliability claim is made. Next: separately frozen blocked-I/O control/effect trial on a fresh owned server.

**Latest main checkpoint (2026-10-23, `b0dba32da`, PR #9420):** PR #9418 integrated the synthetic Win32 caller and custody fixes; #9419 added oracle timestamp-window validation; #9420 repaired private-Xvfb pause cleanup using a retained process descriptor and post-STOP exception cleanup. Their packets preserve local test scopes and failures. Native input/release, live task/MAP01 effect, recovery authority, matched efficiency and reliability remain open.

**Win32 target-generation discriminator (2026-10-23, PR #9435/#9436 and thread-identity follow-up):** `Win32Backend.target_generation()` hashes the configured HWND, GUI-thread ID, owner PID, and process creation time; the reader rechecks both PID and thread ID across the process-time query. The adapter and `create_server()` public-MCP tests confirm a changed HWND or GUI thread within one process is rejected before operation creation or producer start. All 25 focused backend/caller/server tests pass normally and under `python -O`. This is mocked Win32 API composition; reuse of the same numeric HWND on the same thread can still alias, native input remains unqualified, and no WSLc allocation was used.

**WSLc smoke bounded-call repair (2026-10-23, PR #9438):** current main includes merged PR #8503's exact-container cleanup query, but its WSL/WSLc subprocesses had no caller timeout and its `finally` block deleted receipts even when run/cleanup state was unknown. The smoke now bounds version/run/cleanup CLI waits at 10/90/15 seconds, kills only its own timed-out CLI process, retains the unique probe directory and raw stdout/stderr logs after any run/cleanup uncertainty, and returns UNKNOWN without retry. PowerShell parser and child exit/output/timeout tests pass; an offline fake-CLI smoke passes success cleanup, run failure, run timeout, cleanup timeout, and non-empty cleanup retention. No WSLc CLI, container, image, or Docker command was run; #7924 remains STOP/HOLD.

**Local Linux process-only result:** the [R02 packet](../research/integration/xvfb_pidfd_live_20261023_r02/README.md) records one owned Xvfb and three predeclared schedules passing with actual Linux pidfd STOP/CONT calls. Independent observers found healthy stopped/resumed states and resumed states after injected status-read/timer-start faults; target exit and absence were confirmed. The [R01 readiness FAIL](../research/integration/xvfb_pidfd_live_20261023_r01/README.md) is unchanged. R02 uses process-state readiness, not X transport readiness. No GUI input or WSLc operation occurred; this qualifies only this helper process-control sample, not live input release/task effects.

**Oracle observation-window follow-up (`79aa55c0d`):** the [timing packet](../research/integration/win32_oracle_timing_20261023_r01/README.md) reproduces two false successes with stale/future observation timestamps. The caller now requires observation time within the oracle reservation/receipt-processing window and retains both endpoints. All 27 related tests pass normally and under `-O`, including valid endpoint equality and immutable UNKNOWN after rejection. This validates timestamp consistency; it does not independently establish task effect or effect latency.

**Local Win32 supervisor checkpoint (2026-10-23, branch `codex/win32-supervisor-implementation-plan`, `4121be229`):** the approved prestarted-helper model now starts and validates recovery/observer workers before operation admission, then reuses them with operation-scoped result and completion receipts. Public route regressions cover duplicate start/cancel, blocked observation, timeout followed by a late oracle receipt, and separate Generation-A/Generation-B accounting. A fake-API spawned-process test invokes the actual `Win32RuntimeSession` and `Win32Backend.execute()` through blocked-before-acceptance and accepted-before-return schedules; both record producer retirement before recovery UP. A retirement timeout stays UNKNOWN with no recovery UP. The R01 [custody packet](../research/integration/win32_supervisor_custody_20261023_r01/README.md) records 79/79 selected pure/fake tests passing in normal and optimized modes and includes raw output, conditions and source hashes. This branch does not qualify native Windows input, physical release, late-DOWN exclusion, a live task/MAP01 oracle, hard real-time bounds, matched efficiency, or repeated reliability. An earlier broad command accidentally ran the native fixture integration class and failed before a successful emission was recorded; a fixture process query afterward found no remaining process, but this is retained as an unqualified incident because the run does not exclude all native API calls or side effects. Do not rerun that class. No WSLc allocation or Docker was used; #7924 remains STOP/HOLD.

**Joined Win32 caller/backend checkpoint (2026-10-23, `de457b73e`):** the [joined-path R01 packet](../research/integration/win32_public_backend_composition_20261023_r01/README.md) connects public MCP tools to the actual Win32 session/backend through the existing injected producer factory with an inert API. Three new cases cover both blocked-DOWN schedules and unconfirmed producer retirement; all 15 related tests pass normally and under `-O`. An intentionally premature fake UP fails the ordering check. This closes a synthetic test-composition gap; production native adapter, real target identity, physical release, live task effect, efficiency and reliability remain open.

**Current-main Win32 synthetic recheck (2026-10-23, `4c0fe4d31`):** the additive [R02 packet](../research/integration/win32_public_backend_composition_currentmain_20261023_r02/README.md) reruns 48 public-caller, backend-composition, owner, and recovery tests in normal and optimized Python against the current-main tree. Its eight retained public-backend traces pass an independent audit for generation/operation binding, one producer attempt, retirement-before-recovery ordering, UNKNOWN retention, and separate task-effect state. The traces still use inert Win32 APIs; native release, live task effect, WSLc, matched efficiency, and reliability remain unqualified.

**Win32 start-generation repair (2026-10-23, `d06b5d280`):** the [recheck packet](../research/integration/win32_start_generation_recheck_20261023_r01/README.md) reproduces stale/unavailable target generations incorrectly authorizing a producer after admission. The caller now rechecks before factory work and before gate authorization, retains UNKNOWN on failure, and retires a still-gated child without requesting compensating input. Five pre-fix cases fail as expected; 43 related tests pass normally and under `-O`, including cancellation during a blocked generation query. Atomic native target fencing and recovery-time target authority remain open.

**Closed-gate cancellation repair (2026-10-23, `aa891d55f`):** the [new packet](../research/integration/win32_unopened_gate_cancel_20261023_r01/README.md) reproduces an unwanted recovery UP while the final generation query was blocked and the producer gate was still closed. The public caller now declares the gate requirement, and the owner refuses recovery after retiring a never-authorized child. The fixed trace contains only child exit; UNKNOWN/no replay is retained. All 112 focused and compatibility tests pass normally and under `-O`. This is a synthetic-only repair, not native release qualification.

The X11 supervisor remains opt-in. Public-caller live-Xvfb bystander refusal has one scoped test-wrapper sample. For current local Win32 evidence and limits, use the dated checkpoints above and the [supervisor design and qualification record](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md) and [Win32 operation-owner implementation plan](architecture/WIN32_OPERATION_OWNER_IMPLEMENTATION_PLAN.md).

**Prior checkpoint before PR #9408:**

**Repository checkpoint (2026-10-22, historical):** PR #9401 is merged at
`b688ecd3fdb4726b59201f10753ca65d82942b2b`; it preserves the scoped r09
Chromium/App Server polling packet with an explicit source-currency limit. PR
#9402 at `4606c917d22b0da0bd42cdbe7b95fbe606053f5e` records that no complete
r09 source snapshot exists across 48 linked worktrees. PR #9403 at
`375682310fa29d3bd0bf2af71835ef36ab3dc8ac` adds the Win32 operation-owner
plan and confirms the existing owned-process recovery path is X11-specific.
PR #9400 at `632d3603a8df157c1e841dac7ca422c766c77e60` adds a worktree-custody
report. These changes do not alter runtime behavior or the r151 queue
membership. The
user-selected prestarted-supervisor design is already documented in the
canonical [design and qualification record](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md);
it remains opt-in and unqualified at the limits recorded there. The current
organization plan continues from that design and the [worktree custody
report](maintenance/worktree-custody-recheck-20261022-r01.md). A read-only
recheck of the r09 Chromium packet found 316/317 artifact hashes matching
(README changed after its retained audit); all 309 r09 raw files match. Of the
179 frozen source files, 161 match the extant dirty source worktree. A
read-only search across all 48 linked worktrees found no complete source
snapshot: expected versions for 170/179 entries occur somewhere, while nine
were not found. The source worktree remains untouched.

The current Win32 safety follow-up has a separately reviewed
[operation-owner implementation plan](architecture/WIN32_OPERATION_OWNER_IMPLEMENTATION_PLAN.md)
and an [inert prototype packet](../research/integration/win32_operation_owner_prototype_20261022_r01/README.md).
Its r02 synthetic suite passes 12/12 normally and under `-O`; r01's one
expectation failure is retained. The prototype confirms only its own process
ordering. It makes no Windows `SendInput`, physical-release, standard-caller,
or task-success claim; native work remains gated, and #7924 remains STOP.

PR #9404 is merged at `a8f504597ef6a8e097e93dd1cf64611030eea9f7` and retains
the Phase 1 Win32 process-owner model, including the r01 failure and r02
12/12 synthetic pass in normal and optimized mode. A subsequent Phase 2
prerequisite adds a digest of owner PID plus process creation time to the
private Win32 move-reference binding and refuses when identity is missing or
changes before input; related Win32 suites pass locally in both modes. This
still does not connect the owner to the public standard MCP caller:
`mcp_server` has no guarded-Win32 route, and the private MoveBridge remains
synchronous. Bounded release under blocked native I/O, public caller
composition, independent task effect, matched efficiency and reliability
remain open. No native input or WSLc allocation was used; #7924 is OPEN/STOP.

**Current verified functional baseline (2026-10-22):** PR #9397 merged at `b0e8c6c9b4cfb7917932f52e7a69d8267348aa89`, #9398 at `b57e140848087ab814db874f7dfe410926afd387`, and #9399 at current main `08064035460187ba5c8c5cbb2f4e9732ca622ada`. The fresh r151 membership recheck at that SHA has 1,654 open Issues and 452 open PRs, exactly matching r150. PR #9397 adds a public-caller test for terminal receipt archival blocked after cancellation; its scope and limits are in the [supervisor design](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md). Latest runtime behavior remains the bounded MCP-relay cancellation read-ahead from PR #9389, with one deferred ordinary request, one reserved response and fail-closed later dispatch; its relay/Fake X composition suites passed 26/26 in normal and optimized Windows CPython 3.11. PR #9395 adds offline App Server usage reconciliation checks (44/44 related tests in both modes on its exact main source). These are synthetic/local evidence; production provider routing, external usage reconciliation, native/physical release, live MAP01 effect, matched efficiency and broad reliability remain open. PR #8800 remains on an A14 raw-custody hold: its public aggregate is preserved, but the original private report/protocol/images and their owner were not recoverable in the accessible workspace; no rerun was made. The linked-worktree review found 48 worktrees, 14 with changes, including two with thousands of changed entries and unresolved ownership; see the [custody report](maintenance/worktree-custody-recheck-20261022-r01.md). WSLc Issue #7924 remains OPEN/STOP. See [r151](maintenance/repository-inventory-recheck-20261022-r151.md) and the [repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md); cleanup and consolidation records retain historical receipts.

## Historical evidence summaries

PR #9377 adds a research bridge from the existing model-call signature to the provider-attempt ledger and standard public MCP caller. Its injected-model tests preserve wrapper inputs, turn-level usage and JSONL, refuse a stale generation, and retain partial JSONL on timeout without sending a tool call. This is contract/composition evidence only: no real provider run or independent usage-log reconciliation occurred, and #57 remains open.

The active objective is computer control: preserve model-led intent and strategy while qualifying bounded local observation, input release, task-effect checking, and recovery. PR #9346 integrated the retained R02 evidence at `4fd2fe76b516844c89efc2e3fb044dff6ceec5bc`; that Xvfb run used source `cdc8bd6b65bf976137db645c2be31e20090f7d67`. See its packet for the exact historical conditions. Use the [repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md) as the current execution pointer; the [cleanup ledger](REPOSITORY_CLEANUP_PLAN.md) and [consolidation record](REPOSITORY_CONSOLIDATION.md) retain historical receipts and must not be treated as live ownership grants.

Historical current-main addendum after PR #9362 (`df2b41e4a4e0ff03a3a7a139416003bd5599b16`): the [Win32 blocked-SendInput R01 packet](../research/integration/win32_blocked_sendinput_recovery_20261022_r01/README.md) exercises that source's synchronous backend with an inert fake that accepts CTRL-down and blocks before returning. Recovery refuses with no UP while modeled key state remains down; normal and optimized CPython agree. This does not show Windows blocks at that point or establish physical release. The r138 membership pointer and PR #9363 status below applied to that historical checkpoint only; see r146 and the live repository plan above for current cleanup status.

The existing [golden desktop v3 run](../runtime/GOLDEN_DESKTOP_DEMO_V3.md) is a separate real-model integration candidate: one Codex app-server grounding thread completed two image-grounding turns plus one schema preflight; six fixed tasks completed exact-once, all 57 terminal programs verified neutral input, and the old-target pointer was never admitted. Its usage and timing are one persistent-only allocation with only descriptive comparison to retained v1, not a matched public-MCP comparison or reliability estimate. The 232-file/13,805,562-byte retention manifest matches current-main Git blobs. Re-running its source auditor against current main fails its frozen source-hash precondition; this is not a new experiment failure and does not replace the retained outcome. This path shows that a real model-backed desktop route exists. PR #9377 adds a research wrapper bridge, but production model-runner routing, independent provider usage reconciliation, and an integrated live comparison remain open.

Historical membership receipt [r138](maintenance/repository-inventory-recheck-20261022-r138.md) captured main `5a32f1e486b40103a1f24a6059ae78c8cb884e0f` with 1,655 open Issues and 457 open PRs; it is superseded for membership by [r151](maintenance/repository-inventory-recheck-20261022-r151.md). Counts and hashes establish membership only, not semantic disposition. Refresh every live record before changing its state. See the [repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md) for the current execution order and the [cleanup ledger](REPOSITORY_CLEANUP_PLAN.md) for historical queue receipts.

The opt-in prestarted supervisor has two retained current-main WSL2/Xvfb outcomes. R02 passed one standard-caller trial at source `cdc8bd6b65bf976137db645c2be31e20090f7d67`; R03 is an independent repeat at source `6b276fcabfa11c060282e0714501a1057e75c0a6`, merged by PR #9351. Both measured caller admission-to-response below 300 ms, independent key-up readback, and distinct fresh-session synthetic task-oracle success through an 8.5 s horizon; neither promotes the canceled operation from `UNKNOWN`, sets runtime task success, or permits replay. Their separate packets preserve raw conditions and source identity.

A test-only R01 packet then stopped its exact private Xvfb process for 1,500.674 ms. The standard caller returned `pending` 253.566 ms after cancellation admission while Xvfb remained stopped; after resume, supervisor release readback completed in 59.355 ms and an independent client saw all keys up in 98.039 ms. The fresh synthetic task oracle passed, while the old cancellation remained `UNKNOWN` and replay-denied. See the [R01 boundary packet](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-xserver-pause-01/README.md) and [design record](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md). It does not establish release while X11 is stopped, physical desktop/MAP01, matched efficiency, or reliability.


A matched private-Xvfb pilot then ran three no-pause controls and three 1.5 s whole-process pauses on current main `cc5ef16c560cc985ee0951d3d53d659e892f5167`. All six passed the frozen admission-based composite; response ranged 253.263–256.398 ms, and pause-arm independent all-up readback followed resume by 101.874–127.834 ms. Its pre-call harness timestamp includes test setup and a deliberate 50 ms stop-confirmation wait, so actual caller invocation-to-return is unqualified. The synthetic effect oracle passed but exact effect-readback time was not recorded. See the [matched pilot packet](../research/integration/standard_caller_xvfb_current_main_20261022/paused-server-matched-pilot-01/README.md); this is three pairs, not broad reliability or efficiency evidence.

The corrected caller/effect timing instrumentation then passed one unpaused WSL2 private-Xvfb trial on the PR #9354 code. It measured cancellation invocation-to-return at 95.283 ms, input-to-app-event at 37.701 ms, event-to-effect-commit at 0.097 ms, commit-to-independent-readback at 4.937 ms, and input-to-readback at 42.735 ms. The separate synthetic task oracle passed, while the prior cancellation remained UNKNOWN and replay-denied. The [R01 packet](../research/integration/standard_caller_xvfb_current_main_20261022/caller-effect-timing-r01/README.md) preserves raw output, conditions and a PowerShell reconstruction. The outer WSL wrapper returned 1 even on a no-op command; the test subprocess itself returned 0. This is one unpaused synthetic observation, not a matched estimate, broad reliability result, or WSLc evidence.

On exact current main `1263068ac473d6e64bad2136282fcfbf9eab666d`, a clean-worktree local recheck passes 63 supervisor/owned-caller/server-stop tests (one skipped) and 33 ledger/provider-recorder/public-MCP tests in both normal and optimized Python. The [R03 packet](../research/integration/standard_mcp_task_ledger_57_v1/current-main-20261022-r03-local-recheck/README.md) preserves raw output, exit codes, conditions, and source blob IDs. The composed target-generation refusal uses an injected fake provider and the public compiled MCP endpoint. A scoped source search found no matching production provider call site in `runtime`; external usage reconciliation and live-provider task effect remain open.

The supervisor design also retains an open authority gap: the current per-method input lease does not exclude competing X11 clients from global key/button state. Owner-PID absence or supervisor-PID reuse is not sufficient authority for a shared-desktop XTest release. Until an exclusive-input lease is represented and checked, shared-desktop release remains unqualified; see the [design note](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md).

## Current live-XRes bystander result (2026-10-22)

The direct-worker private-Xvfb R01 result remains preserved in its [disposition](../research/integration/live_xres_bystander_reuse_20261022_r01/DISPOSITION.md); R01 of the public-caller packet is separately retained as a preflight-only failure. The later public-caller [R02 disposition](../research/integration/live_xres_public_caller_bystander_20261022_r02/DISPOSITION.md) records one scoped live-Xvfb refusal: natural base reuse, independent PID observation, no release attempt, public result UNKNOWN/no-replay, and independent key-up readback after the delayed horizon. Its audit and source hashes pass. The response time of 251.602 ms is a single descriptive observation, not a hard-bound or reliability estimate. No WSLc/Docker allocation was used.

The public-caller Fake X regression passes in normal and optimized modes; the live-Xvfb caller composition has one scoped pass using a test-only bystander wrapper. It does not prove global input exclusivity. No WSLc allocation is verified; this work used Ubuntu WSL2 only and made no WSLc or Docker operation. Matched efficiency, physical desktop control, MAP01, WSLc portability, and broad reliability remain unqualified. The repository records #17 and #57 as open and #7924 as STOP/HOLD; refresh each live record before any disposition.

On current main `4bcf4e0a9254a8434032e00f6c4965e72c13293d`, a local public-caller target-generation regression recheck passed 20/20 in normal and optimized CPython 3.11.9. It includes fresh-session recovery with the prior UNKNOWN cancellation receipt retained. The adversarial lifecycle check/use race still permits a bounded prefix press after the final local check; the caller then verifies release and refuses retry. This is current-source Fake X evidence, not atomic generation validation or live X11/task-success evidence. See the additive [current-main recheck packet](../research/integration/standard_caller_target_generation_regression_20261022_r01/current-main-20261022-r01/README.md).

X.Org's XTEST protocol accepts a no-delay/relative-millisecond input time, while Xlib `XSync` waits for server processing and X11 has no cross-client request ordering guarantee. This source-backed inference means helper termination bounds caller waiting but does not prove an already accepted request cannot take effect after a deadline. Release-effect bounds during X11 unavailability remain unproven; see the [deadline semantics audit](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#xtest-deadline-semantics-source-audit-2026-10-22). No WSLc allocation was used.
The merged [PR #7181 P01 report](../research/audits/native_three_arm_57_p01_5884_20261004/REPORT.md) is a real three-arm native comparison: persistent input+output was 39,329 tokens versus 109,373 plain and 111,226 ephemeral; ready-to-independent-oracle time was 27.712, 36.631 and 46.550 seconds, respectively. It records 18 independently checked effects and one bounded persistent-path repair. Keep its disposition at HOLD: one fixed-order six-task sample per arm on one known fixture/domain, with model/cache/host-load confounding and limited timing scope. This contributes measured evidence to #57 but does not satisfy the integrated current-caller, second-domain or broad efficiency/reliability gates.

The [r51 navigation coverage audit](maintenance/idea-index-coverage-20261019-r51.md) splits 491 missing primary rows into 20 disjoint discovery batches; it does not classify meaning. See the [repository consolidation plan](REPOSITORY_CONSOLIDATION.md) for family-by-family review and disposition criteria. The first current semantic audit refreshed #6 and #56 against their live Issue records and found the existing [family entry](ideas/reactive-macro-symbolic-interface.md) accurate; both distinct research questions remain open. This page is the short entry point, not an experiment ledger.
The dated [worker dispatch r01](maintenance/worker-dispatch-20261019-r01.md)
records three disjoint family candidates (#17, #5, #59), not current assignments
or resource grants. #17's local Fake X packet is complete. The #5 Fake X
check/use discriminator is now preserved in
[its packet](../research/integration/fake_x_window_lifecycle_check_use_20261019/README.md):
one press can occur after the lifecycle reader retires in the constructed
schedule, followed by refusal and verified Fake X prefix release. This does not
qualify live X ordering or physical release. #59 and every reused work packet
still require live source/owner refresh. Shared indexes remain serially
integrated.

## Objective

Solve computer control: keep intent and strategy with the capable model; use
bounded local observation, input, verification and recovery where they preserve
correctness and reduce waiting, model calls or total resources. Universal
computer control remains available. No component PASS proves the full objective.

## Current maintainer priority

Organize the repository so many workers can find useful, independent work and
deliver it without conflicting instructions, duplicate experiments or lost
evidence. Organize ideas into hypotheses, existing results, dependencies,
priorities and executed tests. Documentation or Issue closure alone does not
resolve a research question. Existing finite/running work keeps its safe boundary.
Use the concise [repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md)
for the current work order; the cleanup ledger and consolidation record remain
the detailed historical receipts.
Repository cleanliness means every active artifact has a traceable disposition,
not that all Issues are closed; see the [current consolidation plan](REPOSITORY_CONSOLIDATION.md#repository-wide-organization-plan-preserve-ideas-enable-parallel-work) and its detailed [family-by-family disposition rules](REPOSITORY_CONSOLIDATION.md#実行計画-r26--アイデアを保全した全体収束).
The first current semantic triage keeps broad reactive-control Issue #6 distinct
from focused symbolic-interface Issue #56; its exact next audit is recorded in
the [family entry](ideas/reactive-macro-symbolic-interface.md) and [work map](WORKER_WORK_MAP.md).
The visual-interface family now separately maps the #4 north star, #3 grid, #5
address/feedback contracts, #7 view-set selection and #8 composite packing; its
finite #7 crosswalk and evidence limits are in the [family agenda](ideas/visual-interface-agenda.md).

The [A02/A03 evidence note](../research/integration/standard_caller_blocked_x11_release_20261019/README.md)
preserves both consumed first outcomes: A02 stopped before probe entry on an
incomplete source mount; A03 passed one healthy control but timed out before
the held-reply predicate. Do not replay them. The offline stream parser has
since been connected to test-only relay/caller composition in merged PRs #9136
and #9153. Local Fake X tests now exercise blocked reply, cancellation,
disconnect, child retirement and a synthetic late queued KeyPress after an
injected separate empty readback. The caller remains `UNKNOWN` and does not
claim task success or permit replay; see the [preserved late-down packet](../research/integration/standard_caller_fake_x_relay_20261019/late-down-after-release-counterexample-20261019-r01/README.md).
The synthetic protocol order is modeled, not live server evidence. A later
[X11 server-ordering source audit](../research/integration/standard_caller_fake_x_relay_20261019/server_disconnect_order_audit_20261019_r01/README.md)
keeps the injected late-down result intact while marking that ordering
unverified; it isolates an XTEST delayed-request case for a version-pinned
Xvfb check. The
additive [same-PID two-connection relay discriminator](../research/integration/offline_proxy_reply_framing_20261019/two-connection-r01/README.md)
forwards a colliding-sequence identity reply while holding only the matching
input reply; parser/relay tests pass 28/28 and standard caller relay composition
passes 3/3 in normal and optimized Python. The standard caller exercises its
identity-query worker through the real target-query and process-identity logic,
backed by shaped synthetic XRes/PID replies; the socket relay carries related
synthetic transaction markers over a second connection. That worker sends
three synthetic request/reply transactions across the second relay before
input. The fixture generation-change case now rejects stale evidence before
either relay sees a KeyPress. It does not exercise XRes wire encoding or live
PID discovery. A03's missing per-connection trace and original failure are
unchanged. Two separate native WSL/Xvfb validations are now retained:
[blocked-I/O release and liveness timestamp](../research/integration/standard_caller_xvfb_blocked_release_20261020/local-native-wsl-r01/README.md)
and [standard-caller target generation and recovery](../research/integration/standard_caller_xvfb_blocked_release_20261020/local-native-wsl-generation-r03/README.md).
They exercise the Linux caller against private synthetic Xvfb applications;
they are not WSLc portability, physical desktop, or MAP01 evidence. The
separate [Windows-host generation/cancellation recheck](../research/integration/standard_caller_windows_generation_cancel_recheck_20261021/README.md)
passes three Fake X standard-caller tests in normal and optimized Python;
stale process/window generations are refused and blocked-owner cancellation
retains UNKNOWN. It does not qualify a live X server, physical input, or task
effect. The [Windows process-start probe](../research/integration/standard_caller_cancel_process_start_20261021/README.md)
measures synchronous event-loop stalls during actual helper startup and
preserves the release gate after unknown disconnect.
The [event-loop cleanup-delay probe](../research/integration/standard_caller_cancel_eventloop_block_20261021/README.md)
separates those injected cleanup waits from real process-start delay; the
[prestarted-supervisor Fake X probe](../research/integration/prestarted_supervisor_fakex_feasibility_20261021/README.md)
is construction feasibility only and does not validate production supervisor
behavior.
The [standard-caller duplicate-cancel retention characterization](../research/integration/standard_caller_duplicate_cancel_retention_20261021/README.md)
compares that production-caller seam with the already-passed independent-owner
duplicate-cancel result in Issue #814: one cleanup attempt occurred, but the
duplicate returned `not_active`, no operation ID or retained cancellation
record was exposed, and the action result remained UNKNOWN. It is one Fake X
trial, not a release guarantee.
The [prestarted cancellation supervisor design](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md)
records the merged opt-in caller path, XRes reuse rule, retained standard-caller
Xvfb outcome, and remaining qualification gates. Its response/transaction
budgets remain experimental targets, not compatibility promises.
The local [public MCP cancellation-operation packet](../research/integration/public_mcp_cancel_operation_registry_20261021/README.md)
now implements one operation ID per call, a dedicated one-worker cancel path,
pending/terminal retention alongside (not inside) the action result, and a
450 ms Fake X caller-response check. Its normal and optimized focused suites
pass 77/77 each. It still has no whole-transaction deadline or prestarted
cleanup process and does not qualify real X11 release, task effect, recovery,
or WSLc.
The [current-main shutdown/cancel-drain probe](../research/integration/standard_caller_shutdown_cancel_drain_20261022/README.md)
found that server lifespan exit stays pending after owner close returns while a
cancellation callback remains blocked; the retained owner-liveness snapshot was
stale against a Win32 PID readback. This is a test-gated Windows Fake X result,
not real X11 release or a general shutdown-time guarantee.
Current-source native-WSL/Xvfb reruns now directly cover two remaining caller
boundaries: [blocked-owner release and delayed-request horizon](../research/integration/standard_caller_xvfb_blocked_release_current_e7_20261021/README.md)
independently observed XTEST keys up in 448 ms while the public caller retained
UNKNOWN; [target-generation/recovery/effect](../research/integration/standard_caller_xvfb_generation_current_e7_20261021/README.md)
refused stale input, recovered in 10 ms, and verified a synthetic application
effect through an independent X client. Both run current source `e7d79d04`,
one trial each, on responsive private Xvfb. Neither covers a stopped X server,
physical desktop, MAP01, reliability population, or matched efficiency.
separate generation-run r01/r02 prelaunch stops are preserved without test
retries. WSLc Issue #7924 remains `STOP / HOLD` for shared ownership; no WSLc
allocation is verified. A future shared WSLc/MAP01 run requires fresh
allocation and ownership evidence. Further local tests should target a concrete
caller/integration decision rather than copy existing parser-only fixtures.
The additive [standard-caller target-generation regression packet](../research/integration/standard_caller_target_generation_regression_20261022_r01/README.md)
records five Fake X caller/lifecycle cases passing in normal and optimized
Windows CPython 3.11.9 at source `c5fd95f38d1e4a780ea0c934da7103dafc3b5e8a`.
It preserves an adversarial destroy-gap schedule where a key prefix can be
emitted after the last local check, then released and locally verified; this
does not make capture-to-press atomic or establish live target generation.

Start with [Worker Quickstart](WORKER_QUICKSTART.md), then select a bounded item
from the [worker work map](WORKER_WORK_MAP.md). The map suggests work; it does not
assign people, grant resources or replace current user instructions.

## Remaining scientific gates

The release-supervision packet preserves main run [39444638512](https://github.com/Unjuno/agent-interface/actions/runs/39444638512), instrumented run [39446039020](https://github.com/Unjuno/agent-interface/actions/runs/39446039020), rebased-head failure [39447636867](https://github.com/Unjuno/agent-interface/actions/runs/39447636867), and fixture-fixed rerun [39448218110](https://github.com/Unjuno/agent-interface/actions/runs/39448218110). r01 retained two `worker_did_not_exit_cleanly` failures among four cancel-retirement comparisons; its receipts discarded child result status. The supervisor diagnostics preserve status and monotonic receipt/exit times while leaving forced termination `UNKNOWN`. r02 had five blocked-owner cases with independent release readback and synthetic-oracle PASS; release took 337–411 ms and cancel 390–654 ms. In r04, all five blocked-owner oracle checks passed (cancel 628–879 ms; release-worker 549–570 ms), with release `UNKNOWN`, runtime `task_success=null`, replay denied. The r03 fixture race was fixed by atomic marker publication and the full Xvfb workflow passed; r03 remains preserved as failure. The separate whole-server-stop task oracle also failed. These results do not establish release while platform I/O is unavailable, physical input, MAP01, or efficiency.

| Gate | Required evidence / next boundary |
|---|---|
| Input authority and release | Fresh target/observation binding, no late new presses, independently verified release and finite recovery under stated faults. Blocking X11 I/O still prevents a universal release-time guarantee. |
| Local continuation and effect | Actual supported caller selects from fresh observations, checks independent application effect, and yields on unknown/stale state. |
| Continuous control / MAP01 | Measured input/release/environment timing, useful response and bounded recovery, with an independently checked task objective. |
| Integrated efficiency | Matched tasks/model/settings and baseline; correctness, all attempts, token/model accounting, latency, resources and failures. |
| Platform transfer | Qualify each supported platform/domain separately; do not transfer a Linux candidate result to Windows or another caller. |

The live parent Issues [#57](https://github.com/Unjuno/agent-interface/issues/57)
(integrated efficiency), [#59](https://github.com/Unjuno/agent-interface/issues/59)
(real-time control), and [#2789](https://github.com/Unjuno/agent-interface/issues/2789)
(usable desktop integration) were rechecked OPEN on 2026-10-19. Their update
timestamps differ; read the latest scope and ownership before shared changes
rather than treating this status check as a fresh assignment.

## Execution and preservation

- Follow the active user's scope and FINAL v5. Ordinary reversible investigation,
  implementation, local tests and authorized integration should proceed autonomously.
- Use the smallest discriminating experiment or repair. Do not repeat a consumed
  formal allocation; preserve first outcomes, raw, frozen conditions and limits.
- Check only resources and ownership needed by the selected operation. A dated
  inventory, open Issue or idle machine is not a resource grant. Closed historical
  logs are context; closing them does not prove release or impose a new global gate.
- Run relevant local validation; do not make optional remote CI a universal wait.
  Obey actual repository permissions/protection. This page adds no reviewer quota.
- Leave executed evidence, resulting decision and a concrete next action. Keep
  ideas open or carry their distinct unresolved work into an actual successor.

## Navigation and history

[Integration gates](INTEGRATION_PLAN.md) · [repository consolidation](REPOSITORY_CONSOLIDATION.md) ·
[ideas and outcomes](IDEAS_AND_OUTCOMES.md) · [research map](RESEARCH_MAP.md) ·
[current interface](../runtime/USING_CURRENT_INTERFACE.md) · [evidence map](EVIDENCE_MAP.md).

The previous 2,219-line document is preserved verbatim in
[CURRENT_GOAL_HISTORY_20261015.md](CURRENT_GOAL_HISTORY_20261015.md).
Its dated directions and allocations are history, not fresh instructions.

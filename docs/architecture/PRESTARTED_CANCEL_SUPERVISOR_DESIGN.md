# Prestarted cancellation supervisor design

Status: proposed for review; no runtime behavior is changed by this document.

## Goal and constraints

Make `interface_guarded_cancel` return within a monotonic caller-response bound while preserving one cancellation/cleanup operation's custody through a finite deadline. A response timeout must remain `UNKNOWN` or `pending`; it must never imply that physical input was released, that the task succeeded, or that input may be replayed. A late or stale cleanup request must not emit a new effect after its deadline or against a different owner generation. The safety path must not depend on planner delivery, image/JSON serialization, ordinary journal persistence, stdout, or event subscribers; critical safety outcomes are recorded best-effort after the action and cannot synchronously delay it.

This design applies to the opt-in `guarded-x11` owned-process path. It preserves FINAL v5 and current execution assignments, keeps `task_success` null absent an independent task oracle, and uses no new WSLc allocation. It does not claim a universal release guarantee when X11 or the OS cannot service input or readback.

## Current source behavior

The public async tool registered in `runtime/cli_v1/mcp_guarded.py` invokes the synchronous closure in `runtime/cli_v1/mcp_server.py`. That closure directly calls `OwnedGuardedSessionOwner.cancel_guarded`, so its waits and process lifecycle work occupy the MCP event-loop thread.

The owner currently uses several independent waits: a 250 ms control response, a separate owner-retirement grace, an XRes query worker, and a release worker. `supervise_xres_worker` in `runtime/guarded_x11_v1/xres_client_fence.py` calls `Process.start()` before starting its worker-response timer. Its existing characterization test explicitly preserves that behavior. Consequently, process creation time is outside the phase timeout and there is no single cancellation deadline. The composed path can exceed its intended response bound and block unrelated MCP requests while cleanup runs.

The current test/evidence boundary is:

| Evidence | What it proves | What remains open |
|---|---|---|
| [`test_supervisor_budget_starts_after_worker_process_creation`](../../runtime/guarded_x11_v1/test_xres_client_fence.py) | Characterizes that worker startup is excluded from the query-response timer. | A single operation-wide deadline, caller/event-loop response bound and late-effect refusal. |
| [`test_cancel_returns_unknown_when_separate_release_worker_blocks`](../../runtime/cli_v1/test_mcp_owned_process.py) | Through the public MCP composition, a blocked Fake X release worker returns an UNKNOWN cleanup classification under the test's three-second allowance. | The test does not measure unrelated MCP work while the cancel handler is waiting or delayed process creation against an absolute deadline. |
| [Standard-caller event-loop probe r02](../../research/integration/standard_caller_cancel_eventloop_block_20261021/README.md) | With two injected 700 ms cleanup-boundary waits, the public MCP cancellation call and maximum heartbeat gap were both 1,406–1,407 ms in all three trials; no-delay controls returned in 0–16 ms. | The injected waits are not actual XRes/process-start delays and the release receipt is deliberately UNKNOWN; this only isolates current synchronous event-loop coupling. |
| [Standard-caller process-start probe r02](../../research/integration/standard_caller_cancel_process_start_20261021/README.md) | Six actual Windows `multiprocessing.spawn` trials through the public MCP caller; one helper start per trial, 172 ms no-delay cancel/heartbeat gap, and 875–891 ms with a 700 ms pre-start delay. The existing 150 ms XRes gate timed out, and release stayed `not_attempted`. | Fake X worker receipts only; this measures real process creation and caller timing, not XRes wire behavior, release, or a product bound. The event loop remains synchronously blocked. |
| [Native-WSL Xvfb r01](../../research/integration/standard_caller_xvfb_blocked_release_20261020/local-native-wsl-r01/README.md) | A separate worker released and independently read back keys while the owned client was blocked in a real `Display.sync()`; cancellation returned in 764 ms. | The caller correctly kept `release_confirmed=false` and cleanup UNKNOWN; this was not a stopped-server, physical desktop, or WSLc result. |
| [Whole-Xvfb-stop r03](../../research/integration/standard_caller_xvfb_server_stop_20261020/pr9247-run-39399107944/README.md) | When the X server itself stopped, the caller returned in 409 ms and preserved UNKNOWN. | XRes timed out, release was not attempted, and independent horizon readback found the held key still down; outage-task score failed. |

Issue [#17 comment 6296321802](https://github.com/Unjuno/agent-interface/issues/17#issuecomment-6296321802) records the same current-main source gap and explicitly leaves release UNKNOWN and replay denied. These outcomes are distinct and remain unchanged; the design must not combine the successful responsive-server case with the failed server-outage case.

## Retained-result seam audit (2026-10-21)

The fetched `main` tip for this audit is `3104de8508f2676242a42847a626db9a4ac82934`; the relevant runtime files are byte-for-byte identical to local source `e7d79d04de46202622873bf116adb909abb0dee2`. `create_server` registers `interface_guarded_cancel` as an async MCP tool, but the registered handler directly returns the synchronous `cancel(call_id)` callback. That callback reads the current `calls` entry under `calls_lock` and then returns `owner.cancel_guarded(call_id)`; it does not write the returned cancellation receipt into the call record or a separate retained file.

`interface_results(call_id)` is the existing read-only retrieval path. It reports `pending` while the original action worker is running. After that worker finishes, it reads the original action's `report.json` (or its interruption receipt) and returns that action outcome with the retained call metadata. Current Fake X tests verify that a cancellation can retire a blocked owner and that the eventual original call result remains conservative. They do not establish a separately retained lifecycle for a cancellation operation that outlives its tool response.

**Decision for the proposal:** keep `interface_results(call_id)` as the sole retrieval endpoint. Give the cancellation transaction its own operation ID and store an additive `cancellation` subrecord in the original call's in-memory registry entry and call directory. The subrecord has `pending`/terminal status, owner generation, absolute deadlines, stage receipts, worker retirement, and uncertainty; it never overwrites the original action report or promotes `task_success`. A call with pending cancellation remains visible through the existing call ID. This avoids a second public tool while preserving the distinction between action and cancellation evidence.

The [standard-caller duplicate-cancel retention characterization](../../research/integration/standard_caller_duplicate_cancel_retention_20261021/README.md) is the current baseline: one release-helper call, but the second request returns `not_active`, no cancellation operation ID is returned, and `interface_results` has no cancellation subrecord. The independent-owner duplicate-cancel PASS in #814 is a separate semantic result and is not repeated here. The next discriminating Fake X validation must exercise a prototype registry/supervisor through the public MCP caller: retrieve the original action while cancellation is pending and after terminal completion, verify separate action/cancellation records, show duplicate requests share one operation ID and one release attempt, and retain `UNKNOWN`/no replay on timeout or stale generation.

The proposed 300 ms caller deadline and 3 s transaction deadline remain unconfirmed tuning values. The feasibility probe supports a construction-level response target only, not a transaction bound or user-visible compatibility guarantee.

## Proposed architecture

Add one narrowly typed, persistent `OwnedCancellationSupervisor` process for each opt-in owned guarded session. Start it and wait for a readiness receipt before admitting guarded input. It owns a command/result channel and accepts only one cancellation transaction; it does not expose generic remote execution. The prestarted process itself performs the bounded XRes disconnect query followed by the one release/readback operation. It does not call `Process.start()` during cancellation, so the transaction has no per-cancel helper-process startup. A synchronous Xlib call that hangs is contained in this helper process, which its parent can terminate at the operation deadline.

Prewarm a dedicated one-worker cancellation executor before serving requests. The async MCP endpoint submits `OwnedGuardedSessionOwner.cancel_guarded` to that executor with `loop.run_in_executor`; it awaits the result only until the caller-response deadline and shields the one in-flight operation from request-task cancellation. The executor thread performs owner control/retirement and communicates with the prestarted cleanup process. The event loop remains available to serve result lookups and unrelated MCP calls. A bounded per-server cancellation map makes repeated cancel calls idempotent and carries a late terminal result into `interface_results`. The request carries:

- a random operation ID and the guarded call ID;
- the immutable owner generation tuple captured from the opened owner (session ID, child PID, X resource base, and binding revision);
- one absolute `deadline_monotonic_ns`, created at cancellation admission;
- the cancellation token and, after owner retirement, the validated owner-input-obligation snapshot.

The supervisor serializes these stages against that same absolute deadline:

1. Request cancellation on the exact active owner using the remaining transaction budget and retain its response or classify it as unconfirmed.
2. Retire the owner when the existing late-server-request or held-input rules require it. Do not reopen or replace it.
3. Send one typed cleanup request to the ready supervisor. The supervisor confirms the exact retired client's XRes disconnect using the captured owner identity.
4. Only after confirmed disconnect and a valid obligation snapshot, attempt one release/readback operation in the same prestarted process. Before connecting or emitting any `KeyRelease`/button-up request, the process checks the original deadline and owner-generation tuple.
5. Retain the stage receipts, supervisor PID/exit evidence, and terminal classification. A missing reply, expired deadline, unsupported identity, blocked server request, supervisor-start failure, or unclean supervisor exit stays `UNKNOWN`.

The MCP caller returns the completed receipt if it arrives in time. If the caller-response deadline expires first, it returns `pending`/`UNKNOWN` with the operation ID and no release claim. The transaction keeps custody; duplicate cancellation calls for the same call ID return the existing operation state and do not enqueue another release. The existing result lookup must expose the retained terminal cleanup receipt after the supervisor finishes. No retry, reconnect, new input, or replay is allowed while cleanup is outstanding or unknown.

Use distinct but nested budgets: the caller-response deadline is shorter than or equal to the transaction deadline. Both are absolute monotonic timestamps derived at admission, not fresh per-phase durations. Proposed initial values are a 300 ms caller wait and a 3 s whole-transaction bound, matching the Fake X construction probe and existing cancellation target. The API response must be returned by 450 ms from admission, allowing the probe's explicit 150 ms scheduling/serialization slack; at the 300 ms caller deadline its state is already `pending`/`UNKNOWN`. These values must be confirmed against current source constants and tested under local load before promotion. Time spent in IPC, process start, owner retirement, XRes, release and reap all consumes the transaction budget.

If the supervisor cannot finish by the transaction deadline, the executor thread terminates it and classifies cleanup `UNKNOWN`; the owner/session becomes unusable and custody metadata is retained. Do not claim that killing the helper retracts requests already queued in the X server. No subsequent owner may inherit the old generation or cleanup receipt. The cleanup helper is retired at owner close when no cancellation consumed it.

## State and compatibility rules

- `release_confirmed` is true only after an accepted release result, clean worker exit, and independent release readback for the exact operation and owner generation.
- Every timeout, malformed receipt, stale generation, process-start delay past deadline, blocked X request, or unclean worker exit yields `release_confirmed=false`, `cleanup_status="UNKNOWN"`, `task_success=null`, and `replay_allowed=false`.
- A bounded caller response and physical release remain separate observations. Returning `pending` does not authorize another input call.
- Existing non-owned and non-X11 modes keep their current cancellation path.
- Existing terminal call receipts and raw attempt evidence remain immutable. New cancellation evidence is additive and names its operation ID, deadlines, stage timestamps, owner generation, worker PIDs/exit codes, readback source, and uncertainty reasons.
- Startup must fail closed for the opted-in mode if the cancellation supervisor cannot become ready; do not silently fall back to synchronous cancellation.

## Validation required before integration

The Fake X feasibility result at `research/integration/prestarted_supervisor_fakex_feasibility_20261021/README.md` only supports the construction concept. Implementation and promotion require these composed tests through the public guarded MCP tools and standard owned caller:

1. Ready supervisor plus injected supervisor-processing delay: MCP returns within the caller-response bound while the cleanup operation remains in custody; if the operation deadline passes before the release boundary, no new Fake X effect appears; caller result stays `UNKNOWN` and replay is denied.
2. Healthy release: exact current generation, one release request, independent Fake X readback up, worker retired, no duplicate effect.
3. Stale generation: reject before release; Fake X state remains down; no retry.
4. Blocked XRes query, blocked release sync, malformed/absent worker receipt, and supervisor/worker exit: bounded caller response, bounded transaction or explicit unreaped-worker classification, no false release claim, session remains unusable.
5. Duplicate cancel while pending and after terminal: same operation receipt, one admitted transaction and at most one release attempt.
6. Event-loop responsiveness while cancellation is pending: an independent MCP observation/result call is serviced without waiting for the cleanup worker.
7. Block receipt write, flush, serialization and stdout delivery independently while cancellation/expiry occurs during held input. Show that safety admission and the release attempt do not wait on those data-plane stalls; retain a compact `DATA_PLANE_BLOCKED` classification and reconstruct order after unblocking.
8. Retain distinct `RELEASE_REQUESTED`, `RELEASE_INJECTED`, `RELEASE_CONFIRMED`, `RELEASE_UNCONFIRMED`, `DATA_PLANE_BLOCKED` and `AUTHORITY_REVOKED` outcomes with cross-plane operation IDs and monotonic timestamps. A timer or receipt write alone cannot produce `RELEASE_CONFIRMED`.
9. Run focused suites in normal and optimized Python. Add a private Xvfb integration only after the Fake X composition is sound; physical desktop, MAP01, WSLc and efficiency remain separate qualifications.

Retain raw receipts, frozen conditions, source revision, process-custody checks and all failed first outcomes. Do not reuse or infer a WSLc allocation from this local design or Fake X result.

## Main risks and unresolved design choices

The prestarted supervisor removes per-cancel child creation from the response path, but it does not make OS scheduling, Xlib requests, or process termination mathematically bounded. The final release boundary must check the absolute deadline because the supervisor may be scheduled late. The existing XRes `(resource_base, PID)` identity is not a cryptographic generation token, so generation fencing must also bind the session ID and permanently retire the session after cancellation. XTest key/button state is global to the X server; the current readback does not prove that the retired owner was the only client holding that key or button. Unless an exclusive-input condition is established independently, a successful global release readback is not sufficient to claim owner-specific release. Cancellation executor capacity must remain one and bounded; timed-out futures cannot create a second concurrent cleanup operation.

This also implements only one possible shape of the separate safety/data-plane split requested by Issue #17. The safety control path must not wait on the existing receipt write path, while compact post-action status may degrade to `DATA_PLANE_BLOCKED`. A two-owner race, planner-controlled release, telemetry lock on cancellation, or false `RELEASE_CONFIRMED` would reject the design even if response timing passed.

Before implementation, confirm whether the proposed 300 ms response / 3 s transaction budgets are acceptable for this opt-in path. The source audit supports `interface_results(call_id)` with a separate additive `cancellation` subrecord; a second public tool is not needed unless a composed Fake X test proves that this existing result path cannot preserve pending and terminal cancellation state independently.

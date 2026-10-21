# Prestarted Cancellation Supervisor Design

**Status:** Design for review; updated with corrected-source Xvfb result r01 and no-input resource-base diagnostic r03. Implementation decisions remain subject to review.

## Problem

The public `interface_guarded_cancel` caller can wait on owner retirement, XRes, and release work in sequence. The current path can block the MCP event loop, and its phase timers do not form one end-to-end deadline. A caller timeout does not prove that input was released or that the original task succeeded. A delayed or stale cleanup must not create a new input effect after cancellation authority expires.

The latest two isolated Xvfb supervisor attempts (39620589667 and 39620978807) failed before XRes and release because the cleanup adapter omitted `owner_generation.child_pid` after owner retirement. This is a construction failure, not a release result. The local PID-source correction passes the four focused Fake X modules in normal and optimized Python.

The first corrected-source local Ubuntu WSL/Xvfb attempt is preserved in [run packet r01](../../../research/integration/public_mcp_prestarted_cancel_supervisor_20261021/xvfb-local-wsl-20261022-r01/README.md). It reached the real blocked Display.sync and built both owner PID fields correctly, then failed closed when XRes returned PID 439 at the retired owner resource base 6291456. The public caller retained UNKNOWN, no XTest release was attempted, and the a obligation remained. Caller response was 43.659 ms and maximum event-loop gap was 5.800 ms; delayed-request-horizon readback and the task oracle were not reached. This local Ubuntu WSL run is not WSLc.

The follow-up no-input [resource-base diagnostic r03](../../../research/integration/public_mcp_prestarted_cancel_supervisor_20261021/xres-base-reuse-local-wsl-20261022-r03/README.md) shows two sources for PID 439: the prestarted helper itself reused the retired owner's base when no bystander was present, and an unrelated replacement process acquired that base when started first. XRes returned the current occupant PID in both cases. The worker returned `stale_owner_identity` with nested `owner_client_disconnect.reason=resource_base_reused`; release remained false, task success null, and replay denied. The r01 socket-permission stop and r02 missing-`xdpyinfo` harness stop are retained separately. This explains the PID mismatch mechanism but does not establish whether a resource-base replacement is sufficient evidence to report owner-client disconnection. Do not infer release or task effect.

There is a current-source contract difference for review. [`wait_for_client_disconnect_supervised`](../../../runtime/guarded_x11_v1/xres_client_fence.py#L175) treats a resource base whose XRes PID differs from the expected owner PID as `disconnected`; its docstring explicitly says the base may belong to another client and that this is not a queue-drained fence or release receipt. [`x11_cancel_worker`](../../../runtime/guarded_x11_v1/cancel_supervisor.py#L235) instead returns `UNKNOWN/stale_owner_identity` with nested `resource_base_reused`, as r03 reproduces. The recommended resolution below keeps this owner-absence receipt separate from release authorization, independent post-release readback, delayed-request exclusion, and task success.

**Recommended resolution:** preserve the existing supervised waiter's narrow meaning after the exact owner process is reaped and the owner-obligation snapshot is available: `disconnected` means the expected owner PID is no longer identified at that XRes resource base. If the base is absent or now identifies a different PID, retain that observation and allow one release attempt for only the captured owner obligations. This is not proof that the X server queue drained, that no other client holds input, or that release succeeded. Keep `release_confirmed=false`, `task_success=null`, and replay denied until independent release readback and the declared delayed-request horizon are satisfied; retain `late_server_request_possible=true` until then. If the expected PID remains at the base through the deadline, or the query/receipt is uncertain, return `UNKNOWN` and do not release. This matches the current standard-caller cleanup gate and preserves the scoped Xvfb release/horizon result while keeping its public result conservative.

## Goals and non-goals

The design should:

- Give each admitted cancellation one operation ID, one owner generation, and one absolute monotonic deadline.
- Keep cancellation custody outside planner delivery, serialization, ordinary receipt writes, stdout, and event subscribers.
- Return control to the MCP event loop within a measured response bound while the operation remains pending or reaches a terminal receipt.
- Refuse stale, expired, duplicate, or post-retirement effects; duplicate requests must reuse the same operation and never start a second release attempt.
- Preserve the original action result and expose cancellation state through the existing `interface_results(call_id)` path.
- Report uncertainty honestly. `UNKNOWN`, `pending`, unreaped worker, or missing readback never means release confirmed, task success, or permission to replay input.

This design does not promise release when the operating system or X server cannot service input or readback. It does not qualify physical desktop control, MAP01, WSLc portability, or matched efficiency. It does not authorize a WSLc allocation.

## Approaches considered

1. **Keep per-cancel child creation.** This preserves the current structure but leaves process startup and multiple phase waits on the response path. The latest source and timing evidence show this does not close the end-to-end bound.
2. **Run cancellation synchronously on the caller.** This makes custody simple but blocks unrelated MCP work while XRes or release is delayed. Existing standard-caller probes establish this event-loop coupling.
3. **Prestart one opt-in supervisor before accepting input.** This removes per-cancel process creation from the cancellation path, gives one owner to the transaction, and can reject admission if readiness is absent. This is the recommended approach, subject to composed fault testing; process scheduling and termination remain best-effort OS operations.

## Proposed behavior

The opt-in `guarded-x11` owned-process path starts one supervisor before input is admitted. Startup must report a typed ready receipt; absent, malformed, or late readiness fails closed before input. The supervisor owns at most one live cancellation transaction per server. Admission atomically binds the operation ID, call ID, session ID, owner generation, and absolute monotonic deadline. A duplicate cancellation for that call returns the same operation identity and retained state.

Cancellation work proceeds independently from the async MCP event loop. The caller returns a pending/unknown receipt within the caller-response bound. The prior proposal's 300 ms caller target and 450 ms outer ceiling are provisional measurement targets, not guarantees; resolve them against the composed implementation and scheduler measurements before promotion. The supervisor checks the same absolute deadline immediately before any release effect. It rejects stale generations, expired work, and replacement cleanup while an earlier worker is unreaped. Session authority is retired after cancellation; timeout, shutdown, or uncertain termination does not make the session reusable.

The existing `interface_results(call_id)` endpoint remains the only retrieval path. It returns the original action record unchanged and an additive cancellation subrecord with operation ID, status, generation, deadline, stage receipts, worker retirement, and uncertainty. It must remain available while the original action is pending and after it terminates. The cancellation record must not overwrite the action report, set `task_success`, or authorize replay.

Safety admission and release must not wait on receipt serialization, disk flush, stdout, telemetry, or event subscribers. Compact terminal status is retained best-effort after the safety action. If that data plane is blocked, record a distinct `DATA_PLANE_BLOCKED`/unknown outcome when possible; do not delay the safety path or synthesize a release confirmation.

## Safety invariants and outcome vocabulary

- One admitted cancellation has one operation ID and at most one release attempt.
- Assign the cancellation deadline at admission. Every stage uses the remaining budget from that same monotonic deadline; no stage resets it.
- Only a current session and owner generation may reach the release boundary.
- `RELEASE_REQUESTED`, `RELEASE_INJECTED`, and `RELEASE_CONFIRMED` are distinct. A timer, process exit, or receipt write alone cannot produce `RELEASE_CONFIRMED`.
- Confirmation requires independent input-state readback after the release attempt, after the frozen delayed-request horizon, and a retired worker. Global XTest state does not establish which client held a key; owner-specific claims require an independently established exclusive-input condition.
- `UNKNOWN`, `pending`, `RELEASE_UNCONFIRMED`, `AUTHORITY_REVOKED`, or `worker_retired=false` denies replay and keeps the session unusable.
- Task success requires an independent task oracle and is separate from release success.

## Failure handling

Startup failure or missing readiness prevents input admission. For a blocked XRes query, blocked release sync/readback, malformed receipt, supervisor exit, caller cancellation, duplicate call, stale generation, expired deadline, shutdown, blocked receipt write, or unreaped worker, the caller response remains bounded and the retained transaction stays explicitly pending/unknown until it reaches a terminal state or records that the worker is unreaped. None may spawn a replacement cleanup while the original operation may still act. Recovery uses a fresh target/session binding and an independent task check; it does not retry the consumed cancellation operation.

The operation deadline bounds admission of new effects, not the time the OS takes to schedule, service, or terminate a process. If a worker remains unreaped, report that fact and retain custody rather than claiming a hard termination bound.

## Validation and promotion gates

1. Corrected-source composed Fake X tests through the public MCP caller prove startup readiness, one operation identity, duplicate reuse, retained results during and after cancellation, and no mutation of the action record.
2. Fault-injection tests cover healthy release; stale and expired authority; delayed supervisor processing; blocked XRes; blocked release sync/readback; malformed or absent receipts; supervisor exit; blocked persistence/stdout; caller cancellation; shutdown; and an unreaped helper.
3. Every case checks both the returned receipt and the independent Fake X effect/state log. A response bound alone is insufficient.
4. Normal and optimized focused suites pass. Preserve the first failing outcome and raw artifacts; do not rerun a consumed formal allocation.
5. Only after the composed Fake X matrix passes, run a new isolated corrected-source Xvfb composition. The no-input r03 diagnostic distinguishes observer-owned and bystander base reuse. After this written spec is reviewed, implement and test the recommended owner-PID-absent receipt contract through the public caller; then separately establish exact release attempt, independent readback after the delayed-request horizon, worker retirement, and a synthetic independent task effect. Keep r01, r02, and r03 immutable.
6. Keep the feature opt-in until these gates pass. Physical desktop, MAP01, WSLc, cross-platform transfer, reliability population, provider accounting, and matched efficiency remain separate qualifications.

## Scope and source of truth

This specification is the reviewable decision summary. The detailed chronology, code seams, historical outcomes, and test references remain in [the architecture and evidence record](../../architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md). Frozen experiment packets and their raw outputs remain authoritative for observed results; this design does not revise them.

Implementation should begin only after this specification is reviewed and any requested corrections are incorporated. Then create a separate task-level implementation plan against the exact source revision and current branch state.

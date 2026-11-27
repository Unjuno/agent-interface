# Guarded response wait budget

Implementation contract at base main 8be8caa39e. Explicit wait_for_result_ms
(0..10000, default null) bounds the local await budget for guarded input or
release-only recovery. It does not change the program, lease, cleanup ownership,
worker execution or authority. Default null preserves the existing full await.

If the actual worker completes within the wait, return its existing result.
Otherwise return pending with the same server-minted call ID, no release/task
confirmation and replay_allowed=false. Register queued custody before submitting
to the executor so an early return still names one discoverable invocation.
Keep the busy slot and shutdown obligation until actual completion; never cancel,
repeat, force-close or reconnect the worker because the response wait ended.
Executor rejection must leave a terminal record and release only unentered work.
Opt-in executor-handle failure/cancellation returns worker_handle_failed with
the same ID and unknown effects. The handle is not the invocation's custody
record: a native writer may still be running. Actual caller/transport cancellation
continues to propagate; it does not cancel accepted worker ownership. Registry
and call IDs belong only to this server process, not restart recovery.

Read interface_results(call_id) for the original result. Other input/recovery/
close requests remain busy while this input owner runs. A queued input may still
start after the pending response; the wait budget does not cancel it. Guarded
cancellation only acknowledges its matching active input context; not_active is
not cancellation confirmation. Pending is neither task failure nor permission
to replay. Completion, release verification and independent task success remain
distinct. Request persistence/presentation may also outlast this wait.

This is a cooperative event-loop wait budget, not a hard response/network/OS time
bound or physical release guarantee. Event-loop/GIL stalls, blocking input send,
sync/readback/close and abrupt process death remain unqualified. A pending native
operation can keep shutdown waiting. Keep custody; transport teardown is not a
recovery strategy. Fake X tests must distinguish held send from fake-neutral
unconfirmed sync/readback, queued work, executor failure and terminal fast paths.

Select explicitly with `interface_guarded_input(..., wait_for_result_ms=20)` or
`interface_guarded_recover_input(current_binding_revision=...,
wait_for_result_ms=20)`. Read `status` first: pending is a wait receipt, not the
input/recovery result. Use its `call_id` with `interface_results`; retrieval
does not dispatch, renew authority or issue a new attempt. A terminal response
that arrives inside the wait retains the existing full/brief presentation rules.
Tests include a separate real stdio client/server with Fake X release-sync
blocked; pending returns before resumption and later lookup obtains the original
failure/release receipt. No frozen collector is rerun to obtain this regression.

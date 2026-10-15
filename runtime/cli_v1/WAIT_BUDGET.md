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

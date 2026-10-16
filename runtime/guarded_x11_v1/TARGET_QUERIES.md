# Experimental active target-query separation

Explicit Python selection:

```python
bridge = NativeHandleBridge(display_name, targets, target, fresh_directory,
                            process_identity=True, query_worker=True)
with bridge.cancellation_scope(unique_token):
    result = bridge.keyboard(alias, offset, tail=authored_tail)
```

The serialized input caller owns the program and cleanup. Another trusted thread
may call `bridge.request_cancel(unique_token)`; it only sets retained local state.
Tokens are consumed once per bridge. Wrong, finished and reused invocation tokens
cannot cancel a new input program. The caller must still inspect execution and
release results. An acknowledgement does not confirm release.

The standard MCP equivalent selects `--session-mode guarded-x11
--guarded-process-identity --guarded-query-worker` at server startup, or
`create_server(..., session_mode='guarded-x11', guarded_process_identity=True,
guarded_query_worker=True)`. These flags are operator policy, not tool arguments.
In this mode `interface_guarded_cancel(call_id=...)` is available outside the
ordinary busy slot. Obtain a running guarded-input ID from `interface_results`;
only that active input context can receive the request. Cancellation makes no
X call, acquires no input authority and performs no filesystem persistence.
Its acknowledgement is not a durable cancellation receipt or input terminal.
Read the original call's result; never replay uncertain input.

During an active guarded input, focus-ancestry and process-incarnation queries
use one separate read-only X connection, opened/read/closed on its own thread.
It uses the input connection's resolved display name, never a later DISPLAY
environment value. The connection must reach the same trusted local server and
PID namespace; this correspondence remains an unauthenticated precondition.
The reader exposes no XTEST/input operations. Requests retain the current target
ID, bridge scope/revision and original program deadline. Context changes,
cancellation, errors and late replies refuse input and require review.

The input thread waits in short Event intervals and services cancellation or
original expiry without waiting for the query to return. Cleanup uses the
original input connection and existing release/readback logic. Read failures or
abandoned requests permanently retire that reader; late replies never publish a
new observation, advance a source, remint an alias or renew authority. The client
closes on its own thread after blocked I/O returns. Closing an owner signals
retirement without joining that thread. Pending/close-error state is reported in
MCP `session.target_queries`. A retired reader requires explicitly closing the
session and starting/reviewing a fresh one; window review cannot reset it.

## Scope and remaining boundaries

This is a named focus/process-query isolation mechanism, **not full observation
or data-plane isolation**. Capture, geometry, `_binding` focus reads, custom input
guard callbacks, JSON persistence, XTEST/send/sync, input readback and connection
close retain their existing synchronous boundaries. For example a custom input
guard that captures while a modifier is held can still block cleanup. This mode
does not weaken those guards or move them onto an unverified cached source.

Python scheduling/GIL stalls, server stalls and input transport/readback stalls
can still delay cleanup. A local fence is not atomic with subsequent server
acceptance. Cancellation immediately after a fence can race in-flight input.
The five-second original guarded lease is not a physical release bound. A stuck
read client may remain alive as a daemon thread until its I/O returns; no forced
socket close, process kill or automatic reconnect is attempted.

Fake X tests execute actual MCP, bridge, capture/handle association, public
dispatch/session/backend, and release tracking. They cover blocked focus and
identity with cancellation/expiry, late-reply retirement, duplicate/wrong/finished
cancel IDs, healthy input and changed process identity. Reader protocol/client
ownership and failure/closure are checked separately. Live same-server ordering,
PID namespaces, real cancellation transport, independent physical release,
application effect, bounded recovery and matched efficiency remain unqualified.
Defaults retain synchronous behavior; no new mode is implicitly enabled.

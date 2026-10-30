# Explicitly owned disposable X11 target processes

`OwnedTargetProcess` is the process-lifecycle primitive for callers that start
their own disposable X11 application. It rejects adoption of caller-supplied
PIDs, shell command strings, non-Linux execution, and environments without
pidfd support. Callers must explicitly pass `disposable=True`.

After launch, bind the target XID while the trusted local X server is
responsive with `bind_x11_target(connection, xid)`. The XRes process identity
must match both the retained `Popen` child and its `/proc` start ticks. Binding
is frozen to one XID. After an outage, `retire_bound_target()` requires no X
connection: it sends SIGTERM and then SIGKILL through the retained pidfd, with
separate bounded waits, and reports `retired` only after the exact child exits.
If identity is missing, ownership is closed, signaling fails, or the deadline
expires, it returns refusal/UNKNOWN without adopting another process. Closing
the ownership handle while the child is still running is refused.

This primitive is not yet connected to `create_server` or the public cancel
receipt. The opt-in private-Xvfb integration test binds a real XRes window to
the launched child, stops that exact X server, and confirms pidfd retirement
of the child before resuming the server. It does not queue delayed input or
measure task effects, and it does not establish public-MCP recovery. See the
current [integration plan](../../docs/INTEGRATION_PLAN.md) for the required
composition and evidence gates.

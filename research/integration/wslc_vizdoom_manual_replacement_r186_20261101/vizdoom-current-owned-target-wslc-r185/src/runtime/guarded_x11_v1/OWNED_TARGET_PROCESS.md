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

An experimental opt-in `create_server` integration binds this handle to one
owned guarded session and attaches retirement evidence to cleanup receipts; see
[owned-target MCP](../cli_v1/OWNED_TARGET_MCP.md). It is not an X11 input
isolation boundary: even a confirmed target exit cannot prevent already held
keys or queued events from reaching other windows on the same display. The
integration's real-app shutdown evidence includes such a counterexample. Task
effects and general recovery remain unproven.

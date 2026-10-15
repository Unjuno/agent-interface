# Experimental active visual-check isolation

Implementation contract, base main 238f211871 (Fake X qualification only).
Explicit observation-worker selection requires target-query/process-identity
selection. Defaults retain existing behavior. One input owner remains; a new
read-only client owns active visual captures, association reads, artifact writes
and trusted additional-input callbacks on its own thread. It never uses the
input connection or publishes owner state. Idle observation remains synchronous.

Each request pins scope, revision, target XID, current sequence, active program
and original deadline. Return only an acquired frame plus verified artifact and
association; publish history/sequence on the input owner only after context,
cancellation and original deadline checks. Retire on error/abandonment; late
replies never publish or renew authority. Worker shutdown never joins blocked I/O.
An abandoned worker can keep running until its dependency returns.

Callbacks remain trusted observational code, now explicitly opted into worker
execution. They receive defensive source/image copies and must not access the
bridge, input connection, input APIs or mutate external/shared state. This is
not a sandbox for arbitrary Python closures. Do not migrate an incompatible
callback implicitly. Preserve visual checks; never replace them with cached
unchecked evidence or share the input connection concurrently.

Verify through actual bridge/MCP plus Fake X: healthy input; capture, artifact
persistence and callback blocked after held modifier × cancel/expiry; stale
association/context/deadline and late-reply refusal; error retirement; own-client
thread ownership, no input operations and distribution import. Retain #8940
as the immutable synchronous baseline. Local normal/-O tests and review precede
integration. No real X, container, input, model or live allocation in this work.

This does not bound input send/sync/readback/close, Python scheduling, memory
operations, pointer transport or arbitrary trusted caller behavior. Local fences
are not atomic with server acceptance. Live server/PID namespace, physical
release, independent application effect, finite recovery and efficiency remain
unqualified. Existing explicit review/recovery policies remain in force.

Select explicitly in Python with `NativeHandleBridge(...,
process_identity=True, query_worker=True, observation_worker=True)`, or at
standard MCP startup with `--session-mode guarded-x11
--guarded-process-identity --guarded-query-worker --guarded-observation-worker`.
The corresponding server constructor option is `guarded_observation_worker=True`.
MCP reports policy and worker state as `session.observation_worker` and
`session.observations`; cancellation still uses the original guarded call ID.
Retired observation readers require closing this session and reviewing a fresh
one. Window review cannot revive a retired reader. A saved observation artifact
from an abandoned request is retained evidence, not a published owner source.
The mode adds one capture client alongside the existing target-query client;
neither is the input connection. Each request carries the current reviewed XID
and resolves a window resource on the capture client's own connection. Successful
window review retains this policy; it does not restore a retired worker.

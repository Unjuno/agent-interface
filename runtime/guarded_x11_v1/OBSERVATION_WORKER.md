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

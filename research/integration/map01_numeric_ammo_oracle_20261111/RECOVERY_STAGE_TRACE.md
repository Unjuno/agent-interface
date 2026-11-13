# Opt-in recovery stage diagnosis

The tracer is an experiment instrument, not a new authority or cancellation
path. Install it explicitly in a dedicated server before spawning helpers.
It wraps existing call sites, retains their arguments/results/exceptions, and
records bounded QPC spans in memory. The helper loop flushes only after normal
shutdown; the server entry point must flush after transport shutdown. A killed
helper may have no trace, which must be reported as missing diagnostics.

Stages cover caller cancellation, the cancel-pending custody write, supervisor
admission, producer retirement, recovery IPC, helper setup/generation checks,
key-UP preparation, the original SendInput call, key readback and first
independent observation. A SendInput return count is insertion evidence only.
Join the API span to the containing key-UP span, exact operation/recovery IDs
and thread to distinguish W-UP from another release. A public recovery receipt,
independent neutral horizon and application effect remain separate evidence.

The absolute timestamps are comparable only after the same-host QPC and child
interpreter preflight passes. Require no dropped spans, valid intervals and all
necessary parent/helper traces before a stage attribution. The timestamp around
an API call is an instrumented call interval, not an OS delivery timestamp.
Tracing itself adds overhead and can alter scheduling; one instrumented trial
cannot prove the cause or exact latency of an earlier uninstrumented run.

R144's retained data place the owner cleanup-request record about 8.993 ms after
expiry and the first neutral sample about 19.460 ms after expiry. Source shows
that the caller writes the already-unresolved custody record before requesting
supervisor cancellation. This motivates measuring the write directly. Do not
relabel its request timestamp as SendInput or infer that moving the write is
safe without checking durable fencing and crash semantics.

The spawn probe starts a real observer helper, reads its ready message and sends
shutdown without an operation. No backend is constructed or input emitted.
Normal and optimized tests also check result identity, exception preservation,
bounded retention, inert recovery receipt parity and an inert SendInput shim.

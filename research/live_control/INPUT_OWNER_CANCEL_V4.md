# Explicit cancellation lane for the owned service

Launch with `launch_owner_service(..., cancellation=True)` to obtain a second
private socket via `take_cancellation_socket()` once. The default remains false.
Construct `CancellationClient(socket, startup=handle.startup, timeout=2)` and call
`watch(original_lease)` before any ordinary input RPC. This explicit hook is
exercised by tests on the actual selected backend/Executor; standard backend
construction and default controller selection have not yet been adapted.

A separate child thread services cancellation independently of the ordinary RPC.
Both decode through one locked `LeaseRegistry`, preserving original v2 intent,
focus/surface/geometry, process generation and deadline. Cancellation registered
before down is sticky. Each lane has its own framing/request IDs; service/display/
owner readiness and service generation bind the private channel. At most64 leases,
64 control requests and1MiB per frame are accepted. A partial control frame that
misses the200ms read deadline retires authority; idle polling does not. Control
loss or invalid generation retires the registry and cancels every known lease.
The cancelled registry cannot admit a subsequent input request.

The parent watcher notices cancellation through a5ms polling wait, independently
of the ordinary RPC worker. It sends a frozen original-source cancellation and
waits for the child's bounded cause result. `wait(intent_token, timeout)` returns
the first outcome; `outcomes` copies all watched results (None if not completed).
`accepted=True` reports acceptance; `release_verified=True` requires a matching
verified native owner release. `accepted=None` means delivery/response is unknown.
They do not grant renewed input authority or prove physical release latency.
Transport/application failures retire the control client and stay unverified.

The child waits up to1s for the exact decoded lease's first interruption. Missing
cause is accepted but unverified. A returned cause is checked against frozen
intent/source/deadline and the original parent Lease's current binding immediately
before application; only cancellation/focus-invalid flags may differ. Parent first
cause must match; `cause_applied=True` records confirmed application. Unverified
but valid cause remains unverified evidence. A later release never overwrites a
first absent/unverified control result. The future backend adapter must retain
that unresolved obligation even if eventual service teardown succeeds.

Send/receive and sender-slot waits each use the explicit finite client timeout;
this is not one end-to-end physical bound. Other simultaneous cancellations can
exhaust the sender deadline, then fail closed by detaching/retiring control.
`close()` stops and joins owned watchers. Startup interruption keeps even a
possibly-started watcher tracked and attempts all cleanup outside the entry lock.
Unresolved start/join raises and retains the handle. This implementation uses
CPython `Thread._started` when resolving interrupted starts; portability to another
Python implementation is unqualified. Fatal and secondary cleanup errors survive.

On service shutdown, `control.json` records control outcomes/error/stop and joins
startup identity. Its SHA256 is stored in recovery, then finish binds recovery.
Control loss yields unverified recovery and nonzero process exit. File-fsync,
exclusive publication and Windows directory/power-loss limits remain those of
[owned service v3](INPUT_OWNER_PROCESS_V3.md). Controller must close ordinary RPC,
then control, then wait on the exact owned service; this is explicit custody.

[Evidence](../integration/owner_cancel_relay_20261016/README.md): Fake X only;
normal/-O each70 methods include original metadata-only counterexamples and the
new independently serviced paths. No native display/input, WSL/container, physical
release-time, shared-input arbitration, task effect or efficiency qualification.
Next under#59: explicit backend/Executor adapter selects both channels, installs
watch before admission, retains failed control/release obligations, propagates
cause/publication failure, and exposes finite shutdown/custody through actual
controller/session death. This relay alone is not that completed adapter.

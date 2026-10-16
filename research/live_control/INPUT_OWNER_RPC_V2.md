# Explicit current-owner RPC v2

`input_owner_rpc_v2.py` is an opt-in connected-socket service boundary around the
current process-aware InputOwner v12 (or its transition wrapper). It creates no
socket, process or display, and is not selected by default session/controller.
The caller must already own the private connected socket and native owner.
Importing this module starts neither input nor background work.

`OwnerRpcClient(sock, display=..., service_id=..., timeout=...)` verifies exact
readiness, process-aware capabilities and strict boolean flags before requests.
`serve_owner(sock, owner, display=..., service_id=...)` requires the actual current
process-aware owner, with no window observer, before publishing readiness.
The service ID binds this channel's logical instance; it is not authentication,
a PID generation proof or a resource grant. No network endpoint is opened.

The codec retains original process/window source tuples, observation sequence,
surface, deadline, focus, geometry and sticky cancel/focus-invalid state. An
existing intent cannot be rebound or renewed. The connected service explicitly
refuses non-null window identity: a canonical observer epoch shared across
capture and input has not been qualified across service processes. Window data
is preserved by the codec, never silently discarded by transport admission.

Allowed operations are `down`, `up`, `up_batch`, `release`, `input_state`, `close`,
with the fixed Doom keyboard allowlist. No pointer API, command execution or
arbitrary callable is accepted. Frames are at most1MiB, one service accepts at
most256 requests and64 lease identities, and requests/replies use strict schemas,
service IDs, monotonically consecutive integer IDs, duplicate-member rejection,
immutable source binding and append-only record snapshots. Ordinary pre-send
validation consumes no request ID. Timeout covers lock admission and socket I/O;
it is a local response deadline, not a native release-time guarantee.

Any post-send transport/protocol/operation failure permanently quarantines the
same client. A timed-out input may already be held. A second framed request is
refused; `close()` detaches the uncertain channel, yielding **unverified** local
cleanup. Server EOF/failure closes the same supplied owner. A normal close
receipt is accepted only when identity, record history, key state and stopped
owner agree; a contradictory or interrupted close remains unverified. Repeated
local close preserves that conservative result without retrying input.

Cancellation is explicit: send `client.call('input_state', lease)` after setting
the caller lease's cancel flag. There is no automatic parent-cancel watcher or
unsolicited record/event delivery. Original deadline and generation monitoring
remain autonomous inside the service's existing owner; `input_state` polls its
records. Therefore this client is **not a drop-in replacement** for current
Executor/backend/session ownership. In particular its `close()` returns a
receipt, whereas a selected owner adapter must raise on unverified cleanup and
preserve the backend custody obligation. Do not substitute it without that
adapter, asynchronous cancellation/telemetry and their composed validation.

Evidence: [retained socket/Fake X packet](../integration/current_owner_rpc_v2_20261016/README.md).
Next: an external service-process launcher and durable identity-bound recovery
receipt, current backend/Executor cancellation and telemetry bridge, then actual
session/controller death composition. Qualify process clock/identity, service
and supervisor death, blocking platform I/O and independent task effects. No
physical device, native display, WSLc allocation, game or model qualification is
provided here. The full computer-control objective remains open under#59.

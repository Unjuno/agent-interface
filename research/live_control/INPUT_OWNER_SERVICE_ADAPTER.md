# Selected backend with owned service custody

The existing `doom_process_identity_backend_v1.Backend` now accepts the explicit
keyword `owner_service=handle` from a cancellation-enabled owned service. Its
default remains the in-process owner. The caller must already own the display;
this API adds no resource permission or automatic launch. Standard V15/controller
CLI selection and controller/session death cleanup remain the next integration.

`OwnedOwnerAdapter` takes each private socket once and owns ordinary RPC, control
watchers and the exact service process handle. It supplies the real owner_id,
stable append-only deduplicated receipt history, `call`, `obligation_snapshot`
and `close`. External construction reuses the same adapter across inherited
backend layers and creates no temporary local input owners. Parent capture and
identity readers are still independent. Window-lifecycle transfer and pointer
programs are refused. Whole-program key/chord/text checks reject unsupported RPC
keys before any earlier step runs; supported text maps spaces to the space key.

Actual inherited binding now reads `surface_context` over ordinary RPC: exact
non-root 32-bit client XID, no Lease, four integer coordinates with nonempty size.
Malformed geometry quarantines the ordinary client. This read grants no input
authority. Capture retains its bracketed parent generation evidence, and the
ordinary service still independently checks the original target before a press.

After backend source binding, adapter freezes the complete original Lease DTO and
starts the cancellation watcher before admission/input. Every leased ordinary
call rechecks the original object and DTO; only cancellation/focus-invalid flags
may change. Mismatch or validation/encoding failure retains a sticky obligation
before send. Restoring fields never restores authority. No failed RPC is retried.

After cancellation of an attempted intent, final release waits a bounded client
timeout for the first control result. Unknown/unverified release or unapplied
cause is retained. Even if the ordinary final cleanup subsequently returns true,
the adapter returns `verified=False` with the original obligation and separately
reports `underlying_cleanup_verified`. The existing Executor records this in its
terminal/backend release obligation and refuses another program or replacement
Executor. Adapter-level obligations also refuse a replacement after close.
Cause publication errors remain with the existing Executor delivery machinery.

`close()` attempts ordinary close, control stop/join, both handle channels and
finite owned-process wait. It returns a receipt binding the real service/owner,
both cleanup results and first obligation. Routine cleanup errors are unverified;
fatal errors preserve paired errors and carry the receipt/owned handle. The first
completed result is immutable. A concurrent close observing unresolved cleanup
retains that uncertainty, so later successful exit cannot upgrade it. Startup
failure attempts all acquired cleanup and attaches `owner_service_handle`.
Late custody inspection uses the same handle; it cannot clear the adapter result.

[Evidence](../integration/owned_backend_adapter_20261016/README.md) uses actual
Backend/Executor and inherited binding, Fake parent/child X, owned Python and
private sockets. Parent local input Display construction is forbidden in the
fixture. Normal/-O each106 methods pass. Real I/O release time, native/window/
pointer coverage, actual task effects and matched economics remain unqualified.
Use the existing#59 for V15/controller opt-in plus controller/session death and
custody receipts; no new coordination/reviewer/allocation gate is introduced.

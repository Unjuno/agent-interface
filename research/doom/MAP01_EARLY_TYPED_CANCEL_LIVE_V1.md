# MAP01 early typed cancellation live v1

This allocation isolates one ordering change from the retained
`map01-running-action-cancel-live-02` baseline. The fixture, seed,
controller-authored held-fire action, visible-ammo invalidation, one episode,
zero model calls and zero retries remain fixed. Session v10 emits a typed
health/ammo event from the captured RGB frame before tile transport and PNG
publication.

The early event binds the exact sequence, capture clock, focus/surface/geometry,
RGB SHA-256 and hash-bound WAD-glyph results. It grants no input authority. The
running guard consumes that event without reopening a PNG. The corresponding
full observation is still encoded, reconstructed and published; the independent
audit must later reopen every PNG and match epoch, binding, RGB hash and both
signal values.

The retained v2 baseline measured 128.488378 ms from invalidating capture to
guard decision, 136.779646 ms to cancel request and 138.693936 ms to verified
release. The frozen v1 thresholds are respectively 60, 75 and 125 ms. Guard
decision must also precede full-artifact readiness. Executor v10 attestation,
one matching cancellation, no later input admission, empty release and clean
process exit remain mandatory.

The single frozen allocation was run once and failed; it was not retried. The
typed path itself became useful early: typed readiness was15.844ms after capture,
cancel was requested at47.529ms, and the exact artifact became ready at119.167ms.
Thus cancel preceded artifact readiness by71.637ms. All three typed/full pairs
reconcile exactly, the program attestation matches, and the owner verified empty
input at50.100ms.

The terminal nevertheless reports `failed / Cancelled()` instead of `cancelled`.
The typed coast backend raises the frozen `executor_v3.Cancelled` class, while
Executor v10 copied and catches a distinct local class with the same name. Its
generic exception path therefore records failure. Terminal release arrived at
128.856ms, exceeding the frozen125ms bound; the exact guard-decision timestamp
and child exit code were not serialized after the wrapper exception. Wrapper
exit is1. Raw evidence, post-control score, owner close, source hashes and the
failed threshold are retained; independent Windows/WSL audit bytes match SHA-256
`fa0fec160f0676fd80420578dbe85c848bae8608fc509028e3345d2570ce07fd`.

This rejects the frozen allocation. A separately versioned repair may reuse the
v3 exception identities while preserving attestation, then freeze a new output
and acceptance rule. It must not modify Executor v10 or retry this allocation.

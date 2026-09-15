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

Construction tests pass, and the preregistration currently verifies with all 21
source hashes and output absence. The live allocation is unrun. A pass would
establish one real reduction in this cancellation path only; it would not prove
planner latency, task completion, gameplay gain or general human-tempo control.

# Executor v10 accepted-program attestation

Executor v10 preserves v3's single owner, no implicit queue, lease, cancellation
and verified release behavior. After deep-copying and validating the entire step
list, and before starting its worker, it computes SHA-256 over canonical JSON for
that immutable snapshot. The `accepted` event returns the digest as
`program_sha256` together with program ID, step count, lease and acceptance time.

Running-action guard v2 independently recompiles the semantic commands and
requires the submitted steps and Executor digest to match that result. A matching
ID and count alone no longer satisfy v35 admission. The digest attests the
validated program snapshot accepted by this Executor process; it does not prove
semantic task correctness or that every step later completed.

`session_map01_v9.py` adopts Executor v10 without modifying hash-bound MAP01
session v7/v8, Executor v3 or the existing coordinate-frame Executor v4. Focused tests verify canonical key ordering and
that caller mutation after submission cannot change the accepted/executed
snapshot.

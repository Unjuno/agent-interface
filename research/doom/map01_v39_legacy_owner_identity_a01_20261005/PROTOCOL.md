# Legacy owner identity projection probe

**H.** In the exact PR #7602 `input_edge_receipts` function, a legacy
`input_release_transition`/`owner_thread_keyup_receipt` row with a conflicting
explicit owner ID in the admission, transition, or nested receipt can still be
reported as `paired` with timing. A minimal compatibility guard should reject
partial or conflicting explicit IDs while retaining ID-free legacy fixtures.

**T.** Freeze PR #7602 head `958dbe99bd27e916ba22a523a1c2c7bbbaf4fc35` and
one real retained V39 admission/release pair. Run the unchanged function and
one patched projection on identical positive, four identity mutations, and an
all-IDs-absent compatibility control in a pinned offline container.

**D.** Baseline should pair the original and all conflicting-ID mutations.
Candidate should pair the original and all-absent compatibility control, while
rejecting each explicit mismatch/partial identity with null timing. Any other
result is a failure or STOP.

**C.** The legacy contract permits rows with no owner ID at all; the candidate
preserves that compatibility. An ID-free row remains weaker evidence than an
identity-bound row and its legacy status semantics are unchanged.

**U.** This is deterministic receipt-projection evidence over one retained event
pair. It is not a new live event, physical-key, application-feedback, recovery,
threat-control, or MAP01 result. No live allocation or candidate runtime ran.

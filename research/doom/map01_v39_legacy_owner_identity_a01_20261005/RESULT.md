# Result

`PASS_LEGACY_OWNER_IDENTITY_CONFLICT_REJECTED_SCOPED` on run 03.

- Exact PR #7602 function: original retained pair and all four identity-corrupted variants return `paired`; each corrupted variant exposes the same non-null timing.
- Candidate projection: original pair and all-owner-IDs-absent legacy control return `paired`; each of four explicit-conflict/partial-identity variants returns `release_receipt_incomplete` with derived timing null.
- Independent raw-only audit: 6 cases, 0 mismatches.
- Candidate and auditor container exits: 0 and 0.

Run 01 is a container-entrypoint STOP with candidate executions 0. Run 02 executed the matrix but failed in post-matrix result collection before writing JSON. Those outcomes are retained and not treated as passes. Run 03 is a distinct fresh construction execution after correcting the harness paths.

Scope: one retained event pair, deterministic identity mutation, projection function only. No live runtime, X server, game, GUI, model, or OS input was used. This confirms an evidence-projection weakness, not mismeasurement of a live episode.
